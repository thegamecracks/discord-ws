from typing import Any, NotRequired, TypedDict


class Event(TypedDict):
    """Represents an event between the client and Discord gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#payload-structure

    """

    op: int
    d: Any
    s: NotRequired[int | None]
    t: NotRequired[str | None]
