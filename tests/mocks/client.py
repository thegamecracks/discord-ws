from unittest.mock import AsyncMock, Mock

import pytest
from discord_ws import Client, Intents
from discord_ws.client import PlainTextStream, Stream, ZLibStream


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
    mock_websocket,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncMock:
    def get_client_stream(client, *args, **kwargs):
        return mock

    mock = AsyncMock(spec_set=Stream)
    monkeypatch.setattr(PlainTextStream, "__new__", get_client_stream)
    monkeypatch.setattr(ZLibStream, "__new__", get_client_stream)
    return mock
