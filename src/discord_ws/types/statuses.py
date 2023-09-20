from enum import StrEnum


class Status(StrEnum):
    """The status of a user.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#update-presence-status-types

    """

    online = "online"
    dnd = "dnd"
    do_not_disturb = "dnd"
    idle = "idle"
    afk = "idle"
    invisible = "invisible"
    offline = "offline"
