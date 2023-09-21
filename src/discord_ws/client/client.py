import asyncio
import inspect
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, cast

import websockets.client
import websockets.frames
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed

from .backoff import Backoff, ExponentialBackoff
from .constants import (
    GATEWAY_CANNOT_RESUME_CLOSE_CODES,
    GATEWAY_CLOSE_CODES,
    GATEWAY_RECONNECT_CLOSE_CODES,
)
from .events import DispatchEvent, Event, Hello, InvalidSession
from .heartbeat import Heart
from .stream import PlainTextStream, Stream, ZLibStream
from discord_ws import constants
from discord_ws.errors import (
    AuthenticationFailedError,
    ConnectionClosedError,
    HeartbeatLostError,
    PrivilegedIntentsError,
)
from discord_ws.http import _create_user_agent
from discord_ws.intents import Intents
from discord_ws.metadata import get_distribution_metadata
from discord_ws.types import GatewayPresenceUpdate

log = logging.getLogger(__name__)

DispatchFunc = Callable[[DispatchEvent], Any]


class Client:
    """The websocket client for connecting to the Discord Gateway."""

    gateway_url: str | None
    """
    The URL to use when connecting to the gateway.

    If this is not provided, it will automatically be fetched
    from the Get Gateway HTTP endpoint during :meth:`Client.run()`.

    """

    token: str
    """The token to use for authenticating with the gateway."""

    intents: Intents
    """The gateway intents to use when identifying with the gateway."""

    user_agent: str
    """The user agent used when connecting to the gateway."""

    compress: bool
    """
    If true, zlib transport compression will be enabled for data received
    by Discord.

    This is distinct from payload compression which is not implemented
    by this library.

    """

    presence: GatewayPresenceUpdate | None
    """The presence for the client to use when identifying to the gateway."""

    _dispatch_func: DispatchFunc | None
    """The function to call when a dispatch event is received.

    This is set by :meth:`on_dispatch()`.

    """

    _heart: Heart
    """The heart used for maintaining heartbeats across connections."""

    _reconnect_backoff: Backoff
    """The backoff function used when reconnecting to Discord."""

    _stream: Stream | None
    """The stream object used for sending and receiving with the current connection.

    This is set by :meth:`_create_stream()`.

    """

    _current_websocket: WebSocketClientProtocol | None
    """
    The current connection to the Discord gateway, if any.

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

    _dispatch_futures: set[asyncio.Future]
    """A set of any future-like objects returned by :attr:`_dispatch_func`.

    This set only exists to maintain a strong reference to each future.
    Once a future is completed, it is automatically removed from the set.

    """

    def __init__(
        self,
        *,
        token: str,
        intents: Intents,
        gateway_url: str | None = None,
        user_agent: str | None = None,
        compress: bool = True,
        presence: GatewayPresenceUpdate | None = None,
    ) -> None:
        """
        :param token:
            The token to use for authenticating with the gateway.
        :param intents:
            The gateway intents to use when identifying with the gateway.
        :param gateway_url:
            The URL to use when connecting to the gateway.
            If this is not provided, it will automatically be fetched
            from the Get Gateway HTTP endpoint during :meth:`Client.run()`.
        :param user_agent:
            An optional user agent used when connecting to the gateway,
            overriding the library's default.
        :param compress:
            If true, zlib transport compression will be enabled for data received
            by Discord. This is distinct from payload compression which is not
            implemented by this library.
        :param presence:
            An optional presence for the client to use when identifying
            to the gateway.

        """
        if user_agent is None:
            user_agent = _create_user_agent(get_distribution_metadata())

        self.gateway_url = gateway_url
        self.token = token
        self.intents = intents
        self.user_agent = user_agent
        self.compress = compress
        self.presence = presence

        self._dispatch_func = None
        self._heart = Heart(self)
        self._reconnect_backoff = ExponentialBackoff()
        self._stream = None

        self._current_websocket = None
        self._resume_gateway_url = None
        self._session_id = None
        self._dispatch_futures = set()

    def on_dispatch(self, func: DispatchFunc | None) -> DispatchFunc | None:
        """Sets the callback function to invoke when an event is dispatched.

        This can be a coroutine function or return an awaitable object.

        """
        self._dispatch_func = func
        return func

    async def run(self, *, reconnect: bool = True) -> None:
        """Begins and maintains a connection to the gateway.

        Use the :meth:`close()` method to gracefully close the connection.

        :param reconnect:
            If True, this method will reconnect to Discord
            where possible.

        """
        if self.gateway_url is None:
            self.gateway_url = await self._get_gateway_url()

        log.debug("Starting connection loop")

        first_connect = True
        while first_connect or reconnect:
            first_connect = False

            if self._can_resume():
                gateway_url = cast(str, self._resume_gateway_url)
                session_id = cast(str, self._session_id)
            else:
                gateway_url = self.gateway_url
                session_id = None
                self._heart.sequence = None

            try:
                async with self._connect(gateway_url) as ws:
                    await self._run_forever(session_id=session_id)
            except ConnectionClosed as e:
                reconnect = self._handle_connection_closed(e) and reconnect
            except HeartbeatLostError as e:
                if not reconnect:
                    raise

            if reconnect:
                duration = self._reconnect_backoff()
                log.debug("Waiting %.3fs before reconnecting", duration)
                await asyncio.sleep(duration)

    async def set_presence(
        self,
        presence: GatewayPresenceUpdate,
        *,
        persistent: bool = True,
    ) -> None:
        """Sets the bot's presence for the current connection, if any.

        :param presence: The payload to be sent over the gateway.
        :param persistent:
            If true, this also sets the :attr:`presence` attribute used
            when reconnecting.

        """
        if self._stream is not None:
            payload: Event = {"op": 3, "d": presence}
            await self._stream.send(payload)
        if persistent:
            self.presence = presence

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

    async def _get_gateway_url(self) -> str:
        from discord_ws import http

        log.debug("Requesting gateway URL")
        async with http.create_httpx_client(token=self.token) as client:
            client.headers["User-Agent"] = self.user_agent
            resp = await client.get("/gateway")
            resp.raise_for_status()
            return resp.json()["url"]

    def _can_resume(self) -> bool:
        return self._resume_gateway_url is not None and self._session_id is not None

    async def _run_forever(self, *, session_id: str | None) -> None:
        async with (
            self._create_stream(),
            self._heart.stay_alive(),
        ):
            if session_id is None:
                await self._identify()
            else:
                await self._resume(session_id)

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
            stream = ZLibStream(self._ws)
        else:
            stream = PlainTextStream(self._ws)

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
        payload = await self._create_identify_payload()
        log.debug("Sending identify payload")
        await self._stream.send(payload)

    async def _create_identify_payload(self) -> Event:
        metadata = get_distribution_metadata()
        d = {
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
        }
        if self.presence is not None:
            d["presence"] = self.presence

        return {"op": 2, "d": d}

    async def _resume(self, session_id: str) -> None:
        """Resumes the given session with Discord.

        .. seealso:: https://discord.com/developers/docs/topics/gateway#resuming

        """
        assert self._stream is not None
        payload = await self._create_resume_payload(session_id)
        log.debug("Sending resume payload")
        await self._stream.send(payload)

    async def _create_resume_payload(self, session_id: str) -> Event:
        return {
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": session_id,
                "seq": self._heart.sequence,
            },
        }

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

            self._heart.sequence = event["s"]

            if event["t"] == "READY":
                self._resume_gateway_url = event["d"]["resume_gateway_url"]
                self._session_id = event["d"]["session_id"]

            self._dispatch(event)

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
            event = cast(InvalidSession, event)
            log.debug("Session has been invalidated")
            if not event["d"]:
                self._invalidate_session()
            await self._ws.close(1002, reason="Invalid Session ACK")

        elif event["op"] == 10:
            # Hello
            event = cast(Hello, event)
            log.debug("Received hello from gateway")
            await self._heart.set_interval(event["d"]["heartbeat_interval"] / 1000)

        elif event["op"] == 11:
            # Heartbeat ACK
            log.debug("Received heartbeat acknowledgement")
            self._heart.acknowledged = True

    def _dispatch(self, event: DispatchEvent) -> None:
        """Dispatches an event using the callback assigned by :meth:`on_dispatch()`."""
        if self._dispatch_func is None:
            return

        ret = self._dispatch_func(event)
        if inspect.iscoroutine(ret) or inspect.isawaitable(ret):
            ret = asyncio.ensure_future(ret)
        if asyncio.isfuture(ret):
            self._dispatch_futures.add(ret)
            ret.add_done_callback(self._dispatch_futures.discard)

    def _invalidate_session(self) -> None:
        self._session_id = None

    def _handle_connection_closed(self, e: ConnectionClosed) -> bool:
        """
        Handles connection closure and either raises an exception or returns
        a boolean indicating if the client is allowed to reconnect.
        """
        if e.rcvd is None and e.sent is None:
            log.info("Connection lost, can reconnect")
            return True
        elif e.sent is not None and not e.rcvd_then_sent:
            # 1000 / 1001 causes our client to appear offline,
            # in which case we probably don't want to reconnect
            reconnect = e.sent.code not in (1000, 1001)
            if reconnect:
                message = "Closed by us with %d, can reconnect"
            else:
                message = "Closed by us with %d, will not reconnect"
            log.info(message, e.sent.code)
            return reconnect
        elif e.rcvd is not None:
            code = e.rcvd.code
            reason = self._get_connection_closed_reason(e.rcvd)

            if code in GATEWAY_CANNOT_RESUME_CLOSE_CODES:
                self._invalidate_session()

            if code not in GATEWAY_RECONNECT_CLOSE_CODES:
                action = "Closed with %s, not allowed to reconnect"
                log.error(action, reason)
                exc = self._make_connection_closed_error(code, reason)
                raise exc from None
            elif self._can_resume():
                action = "Closed with %s, session can be resumed"
                log.info(action, reason)
            else:
                action = "Closed with %s, session cannot be resumed"
                log.info(action, reason)
            return True
        # We only have e.sent, but e.rcvd_then_sent is True?
        log.warning("Ignoring unusual ConnectionClosed exception", exc_info=e)
        return True

    def _get_connection_closed_reason(self, close: websockets.frames.Close) -> str:
        reason = GATEWAY_CLOSE_CODES.get(close.code)
        if reason is not None:
            return f"{close.code} {reason}"
        return str(close)

    def _make_connection_closed_error(
        self,
        code: int,
        reason: str,
    ) -> ConnectionClosedError:
        """Creates an exception for the given close code."""
        if code == 4004:
            return AuthenticationFailedError(code, reason)
        elif code == 4014:
            return PrivilegedIntentsError(
                self.intents & Intents.privileged(),
                code,
                reason,
            )
        return ConnectionClosedError(code, reason)
