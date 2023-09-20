from typing import Self
from unittest.mock import AsyncMock, Mock

import pytest
import websockets.client
from websockets.exceptions import ConnectionClosed
from websockets.frames import Close


class MockWebsocket:
    def __init__(self, mock: Mock) -> None:
        self.mock = mock
        self.closed_with: tuple[int, str] | None = None
        self.rcvd_then_sent: bool | None = None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return

    async def send(self, data: bytes | str) -> None:
        self._check_closed_connection()
        return await self.mock.send(data)

    async def recv(self) -> bytes | str:
        self._check_closed_connection()
        return await self.mock.recv()

    async def close(self, code: int, reason: str = "") -> None:
        await self.mock.close(code, reason)
        self.closed_with = (code, reason)
        self.rcvd_then_sent = False

    def _check_closed_connection(self) -> None:
        if self.closed_with is None:
            return

        rcvd = Close(*self.closed_with)
        sent = Close(*self.closed_with)
        raise ConnectionClosed(rcvd, sent, self.rcvd_then_sent)


def create_websocket() -> MockWebsocket:
    return MockWebsocket(AsyncMock())


@pytest.fixture
def mock_websocket(monkeypatch: pytest.MonkeyPatch):
    def mock_connect(*args, **kwargs):
        return create_websocket()

    monkeypatch.setattr(websockets.client, "connect", mock_connect, raising=False)
