from typing import Any, Literal, NotRequired, TypedDict


class Event(TypedDict):
    """Represents an event between the client and Discord gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#payload-structure

    """

    op: int
    d: NotRequired[Any]
    s: NotRequired[int | None]
    t: NotRequired[str | None]


class DispatchEvent(TypedDict):
    """Represents a dispatch event between the client and Discord gateway."""

    op: Literal[0]
    d: Any
    s: int
    t: str


class InvalidSession(TypedDict):
    """Discord has invalidated the client's session and is requesting a reconnect."""

    op: Literal[9]
    d: bool


class HelloData(TypedDict):
    heartbeat_interval: int


class Hello(TypedDict):
    """Sent by Discord on each new connection providing the heartbeat interval."""

    op: Literal[10]
    d: HelloData
