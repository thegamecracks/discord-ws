from typing import Any, Literal, NotRequired, TypedDict


class Event(TypedDict):
    """Represents an event between the client and Discord gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#payload-structure

    """

    op: int
    d: Any
    s: NotRequired[int | None]
    t: NotRequired[str | None]


class DispatchEvent(TypedDict):
    """Represents a dispatch event between the client and Discord gateway."""

    op: Literal[0]
    d: Any
    s: int
    t: str
