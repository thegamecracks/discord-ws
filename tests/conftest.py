import pytest


@pytest.fixture(autouse=True)
def no_httpx_requests(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delattr("httpx.AsyncClient.send")
