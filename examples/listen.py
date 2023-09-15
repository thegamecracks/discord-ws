import asyncio
import textwrap

import discord_ws

TOKEN = ""
MAX_LENGTH = 100


async def handle_event(event: discord_ws.DispatchEvent):
    data = textwrap.shorten(str(event["d"]), MAX_LENGTH, placeholder="...")
    print(event["t"], "->", data)


async def main():
    client = await discord_ws.Client.create(
        token=TOKEN,
        intents=discord_ws.Intents.standard(),
        on_dispatch=handle_event,
    )

    await client.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
