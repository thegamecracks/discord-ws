import asyncio
import pytest
from unittest.mock import Mock

from discord_ws import HeartbeatLostError
from discord_ws.client import Event, Stream, StreamWebsocket

from tests import raises_exception_group


class HelloThenAcknowledge(Stream):
    def __init__(self, ws: StreamWebsocket) -> None:
        self.ws = ws
        self.sent_hello = False
        self.heartbeats = 0
        self._heartbeat_event = asyncio.Event()

    async def recv(self) -> Event:
        if not self.sent_hello:
            self.sent_hello = True
            return {"op": 10, "d": {"heartbeat_interval": 0.01}}
        await self._heartbeat_event.wait()
        self._heartbeat_event.clear()
        return {"op": 11}

    async def send(self, payload: Event) -> None:
        if payload["op"] == 1:
            self.heartbeats += 1
            self._heartbeat_event.set()


class AllHeartbeatsReceived(BaseException):
    """Raised when all heartbeats have been received."""


class HelloThenLimitedAcknowledge(HelloThenAcknowledge):
    def __init__(self, ws: StreamWebsocket, *, expected_heartbeats: int = 10) -> None:
        super().__init__(ws)
        self.expected_heartbeats = expected_heartbeats

    async def recv(self) -> Event:
        if self.heartbeats >= self.expected_heartbeats:
            raise AllHeartbeatsReceived
        return await super().recv()


class HelloThenBlock(HelloThenAcknowledge):
    async def recv(self) -> Event:
        payload = await super().recv()
        if payload["op"] == 11:
            await asyncio.get_running_loop().create_future()
        return payload


def set_mock_heartbeat(client, client_stream, heartbeat):
    client_stream.recv = heartbeat.recv
    client_stream.send = heartbeat.send
    client._heart._rand = Mock(["random"])
    client._heart._rand.random.return_value = 0


@pytest.mark.asyncio
async def test_normal_heartbeat(client, client_stream):
    heartbeat = HelloThenLimitedAcknowledge(client)
    set_mock_heartbeat(client, client_stream, heartbeat)

    with raises_exception_group((AllHeartbeatsReceived, HeartbeatLostError)):
        async with asyncio.timeout(0.25):
            await client.run(reconnect=False)

    assert heartbeat.heartbeats >= heartbeat.expected_heartbeats


@pytest.mark.asyncio
async def test_lost_heartbeat(client, client_stream):
    heartbeat = HelloThenBlock(client)
    set_mock_heartbeat(client, client_stream, heartbeat)

    with raises_exception_group(HeartbeatLostError):
        async with asyncio.timeout(0.25):
            await client.run(reconnect=False)

    assert heartbeat.heartbeats == 1
