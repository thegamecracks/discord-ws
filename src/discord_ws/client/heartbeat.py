from __future__ import annotations

import asyncio
import json
import logging
import random

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from . import Client

log = logging.getLogger(__name__)


class Heart:
    """Manages the heartbeat loop for a client's connections."""

    interval: float | None
    """
    The heartbeat interval given by Discord.
    This must be set before the heartbeat loop can be started.
    """

    acknowledged: bool
    """
    Indicates if the last heartbeat was acknowledged.

    This is set to False every time a heartbeat is sent.
    If the heart does not receive an acknowledgement before the next
    heartbeat, the heartbeat loop will stop and the connection will
    be terminated.

    This attribute should be updated by the caller.
    """

    sequence: int | None
    """
    The last sequence number received from Discord.

    This attribute should be updated by the caller.
    """

    def __init__(
        self,
        client: Client,
    ) -> None:
        self.client = client

        self.running = False
        self.interval = None
        self.acknowledged = True
        self.sequence = None

        self._beat_event = asyncio.Event()

    async def __aenter__(self) -> Self:
        self.running = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.running = False
        self.interval = None
        self.acknowledged = True
        # self.sequence should not be reset because it needs to persist
        # between connections when resuming

    async def run(self) -> None:
        """Runs the heartbeat loop indefinitely."""
        if not self.running:
            raise RuntimeError(
                "Heartbeat not ready to run; did you use async with heart?"
            )

        while self.running:
            await self._sleep()
            await self._send_heartbeat()

    def beat_soon(self) -> None:
        """Triggers a heartbeat if the heart is currently sleeping."""
        self._beat_event.set()

    async def _sleep(self) -> None:
        """Sleeps until the next heartbeat interval.

        .. seealso:: https://discord.com/developers/docs/topics/gateway#sending-heartbeats

        """
        assert self.interval is not None

        jitter = random.random()
        timeout = self.interval + jitter
        self._beat_event.clear()

        try:
            log.debug("Waiting %.2fs for heartbeat", timeout)
            await asyncio.wait_for(self._beat_event.wait(), timeout)
        except asyncio.TimeoutError:
            pass

    async def _send_heartbeat(self) -> None:
        """Sends a heartbeat payload to Discord."""
        if not self.acknowledged:
            log.debug("Heartbeat not acknowledged, closing connection")
            await self.client._ws.close(1002, reason="Heartbeat ACK lost")

            task = asyncio.current_task()
            assert task is not None
            task.cancel("Last heartbeat was not acknowledged")
            return

        payload = self._create_heartbeat_payload()
        await self.client._ws.send(payload)

        self.acknowledged = False

    def _create_heartbeat_payload(self) -> str:
        log.debug("Sending heartbeat, last sequence: %s", self.sequence)
        payload = {"op": 1, "d": self.sequence}
        return json.dumps(payload)
