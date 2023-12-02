from typing import Any, Literal, NotRequired, TypedDict


class Event(TypedDict):
    """Represents an event between the client and Discord gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#payload-structure

    """

    op: int
    """The gateway opcode indicating the payload type."""
    d: NotRequired[Any]
    """The data for the event."""
    s: NotRequired[int | None]
    """The event's sequence number used for heartbeating and session resumption."""
    t: NotRequired[str | None]
    """The name of the event."""


class DispatchEvent(TypedDict):
    """Represents a dispatch event between the client and Discord gateway."""

    op: Literal[0]
    """The gateway opcode indicating the payload type."""
    d: Any
    """The data for the event."""
    s: int
    """The event's sequence number used for heartbeating and session resumption."""
    t: str
    """The name of the event."""


class InvalidSession(TypedDict):
    """Discord has invalidated the client's session and is requesting a reconnect."""

    op: Literal[9]
    """The gateway opcode indicating the payload type."""
    d: bool
    """The data for the event."""


class HelloData(TypedDict):
    heartbeat_interval: int
    """The heartbeat interval that Discord wants our client to use."""


class Hello(TypedDict):
    """Sent by Discord on each new connection providing the heartbeat interval."""

    op: Literal[10]
    """The gateway opcode indicating the payload type."""
    d: HelloData
    """The data for the event."""
