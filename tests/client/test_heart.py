import asyncio
import logging
import pytest
from unittest.mock import Mock

from discord_ws import HeartbeatLostError

from tests.mocks import client, client_dispatch, client_stream, client_ws


class HelloThenBlock:
    def __init__(self) -> None:
        self.sent_hello = False

    async def __call__(self):
        if not self.sent_hello:
            self.sent_hello = True
            return {"op": 10, "d": {"heartbeat_interval": 0.01}}
        fut = asyncio.get_running_loop().create_future()
        await fut


@pytest.mark.asyncio
async def test_lost_heartbeat(caplog, client, client_stream, client_ws):
    caplog.set_level(logging.DEBUG)
    client_stream.recv = HelloThenBlock()
    client._heart._rand = Mock(["random"])
    client._heart._rand.random.return_value = 0

    with pytest.raises(HeartbeatLostError):
        async with asyncio.timeout(0.25):
            await client.run(reconnect=False)

    client_stream.send.assert_any_call({"op": 1, "d": None})
    client_ws.close.assert_called()
