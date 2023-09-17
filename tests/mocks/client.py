from unittest.mock import AsyncMock, Mock

import pytest
import websockets.client
from discord_ws import Client, Intents
from discord_ws.client import PlainTextStream, Stream, ZLibStream

from .websockets import create_websocket


@pytest.fixture
def client_dispatch() -> Mock:
    return Mock()


@pytest.fixture
def client_stream() -> AsyncMock:
    return AsyncMock(spec_set=Stream)


@pytest.fixture
def client_ws() -> AsyncMock:
    return create_websocket()


@pytest.fixture
def client(
    client_dispatch,
    client_stream,
    client_ws,
    monkeypatch: pytest.MonkeyPatch,
) -> Client:
    def get_client_stream(client, *args, **kwargs):
        return client_stream

    def get_client_ws(*args, **kwargs):
        return client_ws

    client = Client(
        gateway_url="wss://example.invalid",
        token="Bot TOKEN",
        intents=Intents.all(),
        on_dispatch=client_dispatch,
    )

    monkeypatch.setattr(websockets.client, "connect", get_client_ws, raising=False)
    monkeypatch.setattr(PlainTextStream, "__new__", get_client_stream)
    monkeypatch.setattr(ZLibStream, "__new__", get_client_stream)

    return client
