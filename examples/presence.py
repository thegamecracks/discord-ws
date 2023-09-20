import asyncio
import logging

import discord_ws
from discord_ws.types import ActivityType, GatewayPresenceUpdate, Status

TOKEN = "Bot YOUR_TOKEN_HERE"

presence: GatewayPresenceUpdate = {
    "activities": [
        {
            "name": "Hello, World!",
            "type": ActivityType.game,
            "state": "This is a custom status",
            "url": "https://github.com/thegamecracks/discord-ws",
        }
    ],
    "since": None,
    "status": Status.online,
    "afk": False,
}

client = discord_ws.Client(
    token=TOKEN,
    intents=discord_ws.Intents.none(),
    presence=presence,
)

if __name__ == "__main__":
    logging.basicConfig(format="%(name)30s (%(levelname)8s) => %(message)s")
    logging.getLogger("discord_ws").setLevel(logging.DEBUG)
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        pass
