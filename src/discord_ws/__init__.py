from .client import Client, DispatchEvent, Shard
from .errors import (
    AuthenticationFailedError,
    ClientError,
    ConnectionClosedError,
    GatewayInterrupt,
    GatewayReconnect,
    HeartbeatLostError,
    PrivilegedIntentsError,
    SessionInvalidated,
)
from .intents import Intents


def _get_version() -> str:
    from importlib.metadata import version

    return version("discord-ws")


__version__ = _get_version()
