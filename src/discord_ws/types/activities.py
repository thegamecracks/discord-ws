from enum import IntEnum, IntFlag
from typing import NotRequired, TypedDict


class ActivityType(IntEnum):
    """The type of an activity.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-types

    """

    game = 0
    streaming = 1
    listening = 2
    watching = 3
    custom = 4
    competing = 5


class ActivityTimestamps(TypedDict):
    """The unix timestamps for the start and/or end of a game.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-timestamps

    """

    start: NotRequired[int]
    end: NotRequired[int]


class ActivityEmoji(TypedDict):
    """The emoji for an activity.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-emoji

    """

    name: str
    id: NotRequired[int]
    animated: NotRequired[bool]


class ActivityParty(TypedDict):
    """The party for an activity.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-party

    """

    id: NotRequired[int]
    animated: NotRequired[bool]


class ActivityAssets(TypedDict):
    """The assets for an activity.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-assets

    """

    large_image: NotRequired[str]
    large_text: NotRequired[str]
    small_image: NotRequired[str]
    small_text: NotRequired[str]


class ActivitySecrets(TypedDict):
    """The secrets for an activity.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-secrets

    """

    join: NotRequired[str]
    spectate: NotRequired[str]
    match: NotRequired[str]


class ActivityFlags(IntFlag):
    """The flags describing what the activity includes.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-flags

    """

    INSTANCE = 1 << 0
    JOIN = 1 << 1
    SPECTATE = 1 << 2
    JOIN_REQUEST = 1 << 3
    SYNC = 1 << 4
    PLAY = 1 << 5
    PARTY_PRIVACY_FRIENDS = 1 << 6
    PARTY_PRIVACY_VOICE_CHANNEL = 1 << 7
    EMBEDDED = 1 << 8


class ActivityButton(TypedDict):
    """A button to be sent over the gateway for an activity.

    This does not apply to activities received from the gateway.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object-activity-buttons

    """
    label: str
    url: str


class Activity(TypedDict):
    """An activity for a user.

    .. note::

        Bot users are only able to set :attr:`name`, :attr:`state`,
        :attr:`type`, and :attr:`url`.

    .. seealso:: https://discord.com/developers/docs/topics/gateway-events#activity-object

    """

    name: str
    type: int
    url: NotRequired[str | None]
    created_at: NotRequired[int]
    timestamps: NotRequired[ActivityTimestamps]
    application_id: NotRequired[int]
    details: NotRequired[str | None]
    state: NotRequired[str | None]
    emoji: NotRequired[ActivityEmoji | None]
    party: NotRequired[ActivityParty]
    assets: NotRequired[ActivityAssets]
    secrets: NotRequired[ActivitySecrets]
    instance: NotRequired[bool]
    flags: NotRequired[int]
    buttons: NotRequired[list[str | ActivityButton]]
