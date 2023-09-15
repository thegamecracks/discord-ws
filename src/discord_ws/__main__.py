"""A simple command-line interface for connecting to the Discord gateway."""
import argparse
import asyncio
import getpass
import logging
import os

from discord_ws import DispatchEvent
from . import Client, Intents


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--env-token",
    help="Read environment variable instead of prompting for token",
)
intents_group = parser.add_mutually_exclusive_group(required=True)
intents_group.add_argument(
    "--no-intents",
    action="store_const",
    const=Intents.none(),
    dest="intents",
    help="Do not enable any intents",
)
intents_group.add_argument(
    "--standard-intents",
    action="store_const",
    const=Intents.standard(),
    dest="intents",
    help="Enable standard intents",
)
intents_group.add_argument(
    "--all-intents",
    action="store_const",
    const=Intents.all(),
    dest="intents",
    help="Enable standard and privileged intents",
)
intents_group.add_argument(
    "--intents",
    help="The intents value to use as an integer",
    type=lambda s: Intents(int(s)),
)
parser.add_argument(
    "--zlib-stream",
    action="store_const",
    const="zlib-stream",
    dest="compression",
    help="Use zlib transport compression",
)

args = parser.parse_args()

if args.env_token is not None:
    token = os.environ[args.env_token]
else:
    token = getpass.getpass("Token: ")


def event_callback(event: DispatchEvent) -> None:
    pass


async def main():
    client = await Client.create(
        token=token,
        intents=args.intents,
        on_dispatch=event_callback,
        compress=args.compression is not None,
    )

    await client.run()

logging.basicConfig()
logging.getLogger(__package__).setLevel(logging.DEBUG)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
