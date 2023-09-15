import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator, Self, cast

import websockets.client
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

from .constants import (
    GATEWAY_CANNOT_RESUME_CLOSE_CODES,
    GATEWAY_CLOSE_CODES,
    GATEWAY_RECONNECT_CLOSE_CODES,
)
from .events import DispatchEvent, Event
from .heartbeat import Heart
from .stream import PlainTextStream, Stream, ZLibStream
from discord_ws import constants
from discord_ws.http import _create_user_agent
from discord_ws.intents import Intents
from discord_ws.metadata import get_distribution_metadata

log = logging.getLogger(__name__)


class Client:
    """The websocket client for connecting to the Discord Gateway."""

    _current_websocket: WebSocketClientProtocol | None
    """
    The current websocket connection, if any.

    This attribute should not be used directly; see the :attr:`_ws` property.

    """

    _resume_gateway_url: str | None
    """
    The URL to use when resuming gateway connections.

    This is provided during the Ready gateway event.

    """

    _session_id: str | None
    """
    The session ID to use when resuming gateway connections.

    This is provided during the Ready gateway event.

    """

    def __init__(
        self,
        *,
        gateway_url: str,
        token: str,
        intents: Intents,
        user_agent: str | None = None,
        compress: bool = True,
    ) -> None:
        if user_agent is None:
            user_agent = _create_user_agent(get_distribution_metadata())

        self.gateway_url = gateway_url
        self.token = token
        self.intents = intents
        self.user_agent = user_agent
        self.compress = compress

        self._heart = Heart(self)
        self._stream: Stream | None = None

        self._current_websocket = None
        self._resume_gateway_url = None
        self._session_id = None

    @classmethod
    async def create(
        cls,
        *,
        token: str,
        intents: Intents,
        user_agent: str | None = None,
        compress: bool = True,
    ) -> Self:
        """
        A shorthand for creating an :class:`httpx.AsyncClient` and retrieving
        the gateway URL to construct the client.

        :param token:
            The token to use for authenticating with the gateway.
        :param intents:
            The gateway intents to use when identifying with the gateway.
        :param user_agent:
            An optional user agent used when connecting to the gateway,
            overriding the library's default.
        :param compress:
            If true, zlib transport compression will be enabled for data received
            by Discord. This is distinct from payload compression which is not
            implemented by this library.

        """
        from discord_ws import http

        log.debug("Requesting gateway URL")
        async with http.create_httpx_client(token=token) as client:
            resp = await client.get("/gateway")
            resp.raise_for_status()
            gateway_url = resp.json()["url"]

        return cls(
            gateway_url=gateway_url,
            token=token,
            intents=intents,
            user_agent=user_agent or client.headers["User-Agent"],
            compress=compress,
        )

    async def run(self, *, reconnect: bool = True) -> None:
        """Begins and maintains a connection to the gateway.

        Use the :meth:`close()` method to gracefully close the connection.

        :param reconnect:
            If True, this method will reconnect to Discord
            where possible.

        """
        log.debug("Starting connection loop")

        reconnect_argument = reconnect

        connect = True
        reconnect = False

        while connect or reconnect:
            connect = False
            reconnect = False

            if (
                reconnect
                and self._resume_gateway_url is not None
                and self._session_id is not None
            ):
                gateway_url = self._resume_gateway_url
            else:
                gateway_url = self.gateway_url

            try:
                async with self._connect(gateway_url) as ws:
                    await self._run_forever(session_id=self._session_id)
            except ConnectionClosed as e:
                if e.rcvd is None and e.sent is None:
                    reconnect = True
                elif e.sent is not None:
                    # 1000 / 1001 causes our client to appear offline,
                    # in which case we probably don't want to reconnect
                    reconnect = e.sent not in (1000, 1001)
                elif e.rcvd is not None:
                    code = e.rcvd.code
                    code_name = GATEWAY_CLOSE_CODES.get(code)
                    if code_name is None:
                        code_name = str(e.rcvd)
                    else:
                        code_name = f"{code} {code_name}"

                    connect = code in GATEWAY_RECONNECT_CLOSE_CODES
                    reconnect = (
                        connect
                        and code not in GATEWAY_CANNOT_RESUME_CLOSE_CODES
                        and self._session_id is not None
                    )

                    if reconnect:
                        action = "Closed with %s, attempting to resume session"
                        log.info(action, code_name)
                    elif connect:
                        action = "Closed with %s, attempting to reconnect"
                        log.info(action, code_name)
                    else:
                        action = "Closed with %s, cannot reconnect"
                        log.error(action, code_name)

            if not reconnect_argument:
                break

    async def close(self) -> None:
        """Gracefully closes the current connection."""
        await self._ws.close(1000, reason="Going offline")

    @property
    def _ws(self) -> WebSocketClientProtocol:
        """The current websocket connection.

        :raises RuntimeError:
            No websocket connection is currently active.

        """
        if self._current_websocket is None:
            raise RuntimeError(
                "No active websocket connection; did you call Client.run()?"
            )

        return self._current_websocket

    async def _run_forever(self, *, session_id: str | None) -> None:
        async with (
            self._create_stream(),
            self._heart,
            asyncio.TaskGroup() as tg,
        ):
            # We are expecting a hello event here
            # https://discord.com/developers/docs/topics/gateway#hello-event
            await asyncio.wait_for(self._receive_event(), timeout=60.0)
            assert self._heart.interval is not None

            tg.create_task(self._heart.run())

            if session_id is None:
                tg.create_task(self._identify())
            else:
                tg.create_task(self._resume(session_id))

            while True:
                await self._receive_event()

    def _add_gateway_params(self, url: str) -> str:
        """Adds query parameters to the given gateway URL.

        .. seealso:: https://discord.com/developers/docs/topics/gateway#connecting-gateway-url-query-string-params

        """
        import urllib.parse

        params = {
            "v": constants.API_VERSION,
            "encoding": "json",
        }

        if self.compress:
            params["compress"] = "zlib-stream"

        return url + "?" + urllib.parse.urlencode(params)

    @asynccontextmanager
    async def _connect(self, url: str) -> AsyncIterator[WebSocketClientProtocol]:
        """Connects to the gateway URL and sets it as the current websocket."""
        connector = websockets.client.connect(
            self._add_gateway_params(url),
            user_agent_header=self.user_agent,
            # compression=None,
        )

        log.debug("Creating websocket connection")

        async with connector as ws:
            self._current_websocket = ws
            try:
                yield ws
            finally:
                self._current_websocket = None

    @asynccontextmanager
    async def _create_stream(self) -> AsyncIterator[Stream]:
        """Creates the stream to be used for communicating with the gateway."""
        if self.compress:
            stream = ZLibStream(self)
        else:
            stream = PlainTextStream(self)

        self._stream = stream
        try:
            async with stream:
                yield stream
        finally:
            self._stream = None

    async def _identify(self) -> None:
        """Identifies the client with Discord.

        Note that the client can only identify 1000 times in 24 hours,
        and cannot exceed the ``max_concurrency`` threshold specified
        by the Get Gateway Bot endpoint.

        .. seealso:: https://discord.com/developers/docs/topics/gateway#identifying

        """
        assert self._stream is not None

        metadata = get_distribution_metadata()
        payload: Event = {
            "op": 2,
            "d": {
                "token": self.token,
                "intents": self.intents,
                "properties": {
                    "os": sys.platform,
                    "browser": metadata["Name"],
                    "device": metadata["Name"],
                },
                # TODO: payload compression
                # TODO: large_threshold
                # TODO: sharding
                # TODO: presence
            },
        }

        log.debug("Sending identify payload")
        await self._stream.send(payload)

    async def _resume(self, session_id: str) -> None:
        """Resumes the given session with Discord.

        .. seealso:: https://discord.com/developers/docs/topics/gateway#resuming

        """
        assert self._stream is not None
        payload: Event = {
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": session_id,
                "session_id": self._heart.sequence,
            },
        }

        log.debug("Sending resume payload")
        await self._stream.send(payload)

    async def _receive_event(self) -> None:
        """Receives and processes an event from the websocket.

        .. seealso:: https://discord.com/developers/docs/topics/opcodes-and-status-codes#gateway-gateway-opcodes

        """
        assert self._stream is not None
        event = await self._stream.recv()

        if event["op"] == 0:
            # Dispatch
            event = cast(DispatchEvent, event)
            log.debug("Received %s event", event["t"])

            if event["t"] == "READY":
                self._resume_gateway_url = event["d"]["resume_gateway_url"]
                self._session_id = event["d"]["session_id"]

        elif event["op"] == 1:
            # Heartbeat
            log.debug("Received request to heartbeat")
            self._heart.beat_soon()

        elif event["op"] == 7:
            # Reconnect
            log.debug("Received request to reconnect")
            await self._ws.close(1002, reason="Reconnect ACK")

        elif event["op"] == 9:
            # Invalid Session
            log.debug("Session has been invalidated")
            await self._ws.close(
                1002 if event["d"] else 1000,
                reason="Invalid Session ACK",
            )

        elif event["op"] == 10:
            # Hello
            log.debug("Received hello from gateway")
            self._heart.interval = event["d"]["heartbeat_interval"] / 1000

        elif event["op"] == 11:
            # Heartbeat ACK
            log.debug("Received heartbeat acknowledgement")
            self._heart.acknowledged = True
