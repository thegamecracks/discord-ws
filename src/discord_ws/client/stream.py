from __future__ import annotations

import json
import zlib

from typing import TYPE_CHECKING, Any, NotRequired, Protocol, Self, TypedDict

if TYPE_CHECKING:
    from . import Client

Z_SYNC_FLUSH = b"\x00\x00\xff\xff"


class Event(TypedDict):
    """Represents an event between the client and Discord gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#payload-structure

    """

    op: int
    d: Any
    s: NotRequired[int | None]
    t: NotRequired[str | None]


class Stream(Protocol):
    """Manages receiving and sending events between the client and Discord gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway#encoding-and-compression

    """

    client: Client

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

    def __init__(self, client: Client) -> None:
        self.client = client

    async def recv(self) -> Event:
        while True:
            data = await self.client._ws.recv()
            return json.loads(data)

    async def send(self, payload: Event) -> None:
        data = json.dumps(payload)
        await self.client._ws.send(data)


class ZLibStream(Stream):
    """Implements a gateway stream with zlib transport compression."""

    def __init__(self, client: Client) -> None:
        self.client = client

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
            data = await self.client._ws.recv()

            assert isinstance(data, bytes)
            assert self._decompress_buffer is not None
            assert self._decompress_obj is not None

            self._decompress_buffer += data
            if not data.endswith(Z_SYNC_FLUSH):
                continue

            data = self._decompress_obj.decompress(self._decompress_buffer)
            self._decompress_buffer.clear()

            data = data.decode("utf-8")
            return json.loads(data)

    async def send(self, payload: Event) -> None:
        data = json.dumps(payload)
        await self.client._ws.send(data)
