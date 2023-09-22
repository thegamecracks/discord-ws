from .client import Client, DispatchEvent
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

__version__ = "0.2.0"
