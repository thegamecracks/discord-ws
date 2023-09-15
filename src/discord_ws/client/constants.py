GATEWAY_CLOSE_CODES = {
    4000: "Unknown Error",
    4001: "Unknown Opcode",
    4002: "Decode Error",
    4003: "Not Authenticated",
    4004: "Authentication Failed",
    4005: "Already Authenticated",
    4007: "Invalid Sequence",
    4008: "Rate Limited",
    4009: "Session Timed Out",
    4010: "Invalid Shard",
    4011: "Sharding Required",
    4012: "Invalid API Version",
    4013: "Invalid Intents",
    4014: "Disallowed Intents",
}
"""
A mapping of close codes recognized by Discord.

.. seealso:: https://discord.com/developers/docs/topics/opcodes-and-status-codes#gateway-gateway-close-event-codes
"""

GATEWAY_RECONNECT_CLOSE_CODES = (
    4000,
    4001,
    4002,
    4003,
    4005,
    4006,
    4007,
    4008,
    4009,
)
"""
A sequence of close codes where the client is allowed to reconnect
and potentially resume the last session.
"""

GATEWAY_CANNOT_RESUME_CLOSE_CODES = (
    4007,
    4009,
)
"""A sequence of close codes where the client must reset its current session."""
