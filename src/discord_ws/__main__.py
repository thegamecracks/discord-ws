import asyncio
import logging
import os

from . import Client, Intents

token = os.environ["TOKEN"]


async def main():
    logging.basicConfig()
    logging.getLogger(__package__).setLevel(logging.DEBUG)

    client = await Client.create(
        token=token,
        intents=Intents.all(),
    )

    await client.run()


asyncio.run(main())
