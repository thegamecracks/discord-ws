from __future__ import annotations

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator, Self

if TYPE_CHECKING:
    from . import Client, Event

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

        self.interval = None
        self.acknowledged = True
        self.sequence = None

        self._beat_event = asyncio.Event()
        self._rand = random.Random()

    @asynccontextmanager
    async def stay_alive(
        self,
        *,
        wait_for_event: bool = True,
    ) -> AsyncIterator[Self]:
        """A context manager that keeps the heart alive.

        The client must have a connection established before this
        context manager can be used.

        After exiting, the interval is cleared and must be reset again.

        If the heartbeat is not acknowledged, the connection will be closed
        and the current task cancelled.

        :param wait_for_event:
            When true, waits for an event to be received before starting
            the heartbeat loop. At the start of a connection, this should
            be the HELLO event that sets the heartbeat interval.
        :raises asyncio.TimeoutError:
            No event was received while waiting for an event.

        """
        try:
            if wait_for_event:
                await asyncio.wait_for(self.client._receive_event(), timeout=60.0)

            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._run())
                yield self
        finally:
            self.interval = None
            self.acknowledged = True
            # self.sequence should not be reset because it needs to persist
            # between connections when resuming

    async def _run(self) -> None:
        """Runs the heartbeat loop indefinitely."""
        while True:
            await self._sleep()
            await self._send_heartbeat()

    def beat_soon(self) -> None:
        """Skips the current interval to trigger the next heartbeat."""
        self._beat_event.set()

    async def _sleep(self) -> None:
        """Sleeps until the next heartbeat interval.

        .. seealso:: https://discord.com/developers/docs/topics/gateway#sending-heartbeats

        """
        assert self.interval is not None

        jitter = self._rand.random()
        timeout = self.interval + jitter

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

        assert self.client._stream is not None

        payload = self._create_heartbeat_payload()
        log.debug("Sending heartbeat, last sequence: %s", self.sequence)
        await self.client._stream.send(payload)

        self._beat_event.clear()
        self.acknowledged = False

    def _create_heartbeat_payload(self) -> Event:
        return {"op": 1, "d": self.sequence}
