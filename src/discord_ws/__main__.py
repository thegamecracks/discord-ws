import asyncio
import os

from . import Client, Intents

token = os.environ["TOKEN"]


async def main():
    client = await Client.create(
        token=token,
        intents=Intents.all(),
    )

    await client.run()


asyncio.run(main())
