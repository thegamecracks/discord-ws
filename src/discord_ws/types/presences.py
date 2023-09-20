from typing import TypedDict

from .activities import Activity


class GatewayPresenceUpdate(TypedDict):
    """The payload used for updating the client's current presence via the gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#update-presence

    """

    since: int | None
    activities: list[Activity]
    status: str
    afk: bool
