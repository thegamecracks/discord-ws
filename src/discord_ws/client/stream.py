import json
import logging
import zlib
from typing import Any, Protocol, Self

from .events import Event

log = logging.getLogger(__name__)

Z_SYNC_FLUSH = b"\x00\x00\xff\xff"


def _get_data_type(data: bytes | str) -> str:
    if isinstance(data, str):
        return "chars"
    return "bytes"


class StreamWebsocket(Protocol):
    """The websocket interface to be wrapped by :class:`Stream`."""

    async def recv(self) -> bytes | str:
        ...

    async def send(self, data: bytes | str, /) -> Any:
        ...


class Stream(Protocol):
    """Manages receiving and sending events between the client and Discord gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway#encoding-and-compression

    """

    ws: StreamWebsocket

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> Any:
        return None

    async def recv(self) -> Event:
        """
        Continuously receives data from the client's websocket until
        a payload can be parsed.
        """
        ...

    async def send(self, payload: Event) -> None:
        """Sends a payload through the websocket.

        Note that the payload should not exceed 4096 bytes when encoded in UTF-8.

        .. seealso:: https://discord.com/developers/docs/topics/gateway#sending-events

        """
        ...


class PlainTextStream(Stream):
    """Implements a gateway stream with no transport or payload compression."""

    def __init__(self, ws: StreamWebsocket) -> None:
        self.ws = ws

    async def recv(self) -> Event:
        data = await self.ws.recv()
        log.debug("Received %d %s", len(data), _get_data_type(data))
        return json.loads(data)

    async def send(self, payload: Event) -> None:
        data = json.dumps(payload)
        await self.ws.send(data)


class ZLibStream(Stream):
    """Implements a gateway stream with zlib transport compression."""

    def __init__(self, ws: StreamWebsocket) -> None:
        self.ws = ws

        self._decompress_obj: zlib._Decompress | None = None
        self._decompress_buffer: bytearray | None = None

    async def __aenter__(self) -> Self:
        self._decompress_obj = zlib.decompressobj()
        self._decompress_buffer = bytearray()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._decompress_buffer = None
        self._decompress_obj = None

    async def recv(self) -> Event:
        while True:
            data = await self.ws.recv()

            assert isinstance(data, bytes)
            assert self._decompress_buffer is not None
            assert self._decompress_obj is not None

            log.debug("Buffering %d bytes", len(data))
            self._decompress_buffer += data
            if not data.endswith(Z_SYNC_FLUSH):
                continue

            log.debug("Decompressing %d bytes", len(self._decompress_buffer))
            data = self._decompress_obj.decompress(self._decompress_buffer)
            self._decompress_buffer.clear()

            data = data.decode("utf-8")
            return json.loads(data)

    async def send(self, payload: Event) -> None:
        data = json.dumps(payload)
        log.debug("Sending %d %s", len(data), _get_data_type(data))
        await self.ws.send(data)
