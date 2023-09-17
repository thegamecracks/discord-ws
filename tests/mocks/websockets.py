from unittest.mock import AsyncMock


def create_websocket() -> AsyncMock:
    mock = AsyncMock()
    mock.__aenter__.return_value = mock
    return mock
