from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord_ws.intents import Intents


class ClientError(Exception):
    """The base class for exceptions raised by the client."""


class ConnectionClosedError(ClientError, ConnectionError):
    """An error caused the connection to close."""

    code: int
    """The close code that triggered this exception."""

    reason: str
    """The reason provided for this closure."""

    def __init__(self, code: int, reason: str) -> None:
        super().__init__(f"{code} {reason}")
        self.code = code
        self.reason = reason


class AuthenticationFailedError(ConnectionClosedError):
    """The client failed to authenticate with Discord."""

    def __str__(self) -> str:
        return "Discord rejected your credentials. Is your token correct?"


class PrivilegedIntentsError(ConnectionClosedError):
    """The client requested privileged intents that were not enabled."""

    required_intents: Intents
    """The privileged intents requested by the client."""

    def __init__(self, required_intents: Intents, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.required_intents = required_intents

    def __str__(self) -> str:
        intents = ", ".join([str(i.name) for i in self.required_intents])
        return (
            "Discord rejected your requested intents.\n"
            "Go to the developer portal at https://discord.com/developers/applications\n"
            "and make sure you have enabled these intents: {}\n"
        ).format(intents)


class GatewayInterrupt(ClientError):
    """
    The client has been asked by the gateway to interrupt the current connection.

    This exception and its subclasses are expected to be raised during normal
    operation, and should not impact the client's ability to reconnect to the
    gateway.

    """


class GatewayReconnect(GatewayInterrupt):
    """The client has been asked to reconnect to the gateway.

    This corresponds with the Reconnect (9) opcode.

    """

    def __init__(self) -> None:
        super().__init__("Discord has requested our client to reconnect.")


class SessionInvalidated(GatewayInterrupt):
    """The client's session has been invalidated by the gateway.

    This corresponds with the Invalid Session (9) opcode.

    """

    resumable: bool
    """Indicates if the session can be resumed."""

    def __init__(self, resumable: bool) -> None:
        super().__init__("Discord has invalidated our session.")
        self.resumable = resumable


class HeartbeatLostError(ClientError):
    """A heartbeat acknowledgement from the server was missed."""

    def __init__(self) -> None:
        super().__init__("Discord was not able to acknowledge our heartbeat.")
