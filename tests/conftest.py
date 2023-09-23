import logging

import pytest

from tests.mocks import client, client_dispatch, client_stream, mock_websocket


@pytest.fixture(autouse=True)
def enable_logging(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.DEBUG, "discord_ws")


@pytest.fixture(autouse=True)
def no_httpx_requests(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delattr("httpx.AsyncClient.send")


@pytest.fixture(autouse=True)
def no_websockets_connect(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delattr("websockets.client.connect")
