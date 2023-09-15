import asyncio
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator, Self

import websockets.client
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

from .heartbeat import Heart
from .stream import Event, PlainTextStream, Stream, ZLibStream
from discord_ws import constants
from discord_ws.http import _create_user_agent
from discord_ws.intents import Intents
from discord_ws.metadata import get_distribution_metadata


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

    async def run(self) -> None:
        """Begins a connection to the gateway and starts receiving events."""
        async for ws in self._connect_forever():
            try:
                await self._run_forever()
            except ConnectionClosed:
                raise NotImplementedError

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

    async def _run_forever(self) -> None:
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
            tg.create_task(self._identify())

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

    async def _connect_forever(self) -> AsyncIterator[WebSocketClientProtocol]:
        """Returns an iterator for connecting to the websocket indefinitely."""
        connector = websockets.client.connect(
            self._add_gateway_params(self.gateway_url),
            user_agent_header=self.user_agent,
            # compression=None,
        )

        async for ws in connector:
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
            },
        }

        await self._stream.send(payload)

    async def _receive_event(self) -> None:
        """Receives and processes an event from the websocket.

        .. seealso:: https://discord.com/developers/docs/topics/opcodes-and-status-codes#gateway-gateway-opcodes

        """
        assert self._stream is not None
        event = await self._stream.recv()

        if event["op"] == 0:
            # Dispatch
            raise NotImplementedError

        elif event["op"] == 1:
            # Heartbeat
            self._heart.beat_soon()

        elif event["op"] == 7:
            # Reconnect
            raise NotImplementedError

        elif event["op"] == 9:
            # Invalid Session
            raise NotImplementedError

        elif event["op"] == 10:
            # Hello
            self._heart.interval = event["d"]["heartbeat_interval"]

        elif event["op"] == 11:
            # Heartbeat ACK
            self._heart.acknowledged = True
