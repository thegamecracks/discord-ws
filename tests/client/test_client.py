import pytest

from discord_ws import GatewayReconnect, SessionInvalidated

from tests import raises_exception_group
from tests.mocks import client, client_stream, mock_websocket


@pytest.mark.asyncio
async def test_gateway_reconnect(client, client_stream, mock_websocket):
    client_stream.recv.return_value = {"op": 7}

    with raises_exception_group(GatewayReconnect):
        await client.run(reconnect=False)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{"op": 9, "d": False}, {"op": 9, "d": True}])
async def test_session_invalidation(payload, client, client_stream, mock_websocket):
    client_stream.recv.return_value = payload

    with raises_exception_group(SessionInvalidated):
        await client.run(reconnect=False)
