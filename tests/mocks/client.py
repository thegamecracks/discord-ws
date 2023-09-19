from unittest.mock import AsyncMock, Mock

import pytest
import websockets.client
from discord_ws import Client, Intents
from discord_ws.client import PlainTextStream, Stream, ZLibStream

from .websockets import create_websocket


@pytest.fixture
def client() -> Client:
    client = Client(
        gateway_url="wss://example.invalid",
        token="Bot TOKEN",
        intents=Intents.all(),
    )
    return client


@pytest.fixture
def client_dispatch(client) -> Mock:
    mock = Mock()
    client.on_dispatch(mock)
    return mock


@pytest.fixture
def client_stream(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncMock:
    def get_client_stream(client, *args, **kwargs):
        return mock

    mock = AsyncMock(spec_set=Stream)
    monkeypatch.setattr(PlainTextStream, "__new__", get_client_stream)
    monkeypatch.setattr(ZLibStream, "__new__", get_client_stream)
    return mock


@pytest.fixture
def client_ws(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncMock:
    def get_client_ws(*args, **kwargs):
        return ws

    ws = create_websocket()
    monkeypatch.setattr(websockets.client, "connect", get_client_ws, raising=False)
    return ws
