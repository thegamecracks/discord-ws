# discord-ws

A bare-bones asynchronous Python wrapper for the Discord Gateway API.

> [!NOTE]
>
> This library is **not** associated with [discord-ws](https://pypi.org/project/discord-ws/)
> on PyPI, which is written by a different author. For now, I am not planning
> to release this project on PyPI.

## Usage

Assuming you have Python 3.11+ and Git installed, you can install this library
with:

```sh
pip install git+https://github.com/thegamecracks/discord-ws
```

If you want to test out the library without writing a script, create a bot
on Discord's [Developer Portal], copy your bot token, and try out the built-in CLI:

```sh
python -m discord_ws --standard-intents --zlib-stream
```

If you do want to write a script, import the library and use the [Client]
class to establish a connection yourself:

```py
import asyncio
import discord_ws

async def main():
    client = await discord_ws.Client.create(
        token="Bot YOUR_TOKEN_HERE",
        intents=discord_ws.Intents.standard(),
        on_dispatch=handle_event,
    )

    await client.run()

async def handle_event(event: discord_ws.DispatchEvent):
    ...  # Do something with the events received from Discord

asyncio.run(main())
```

[Developer Portal]: https://discord.com/developers/applications
[Client]: https://github.com/thegamecracks/discord-ws/blob/main/src/discord_ws/client/client.py

## Resources

- Discord Docs: https://discord.com/developers/docs/topics/gateway
- Websockets Library: https://websockets.readthedocs.io/en/stable/index.html

## License

This project is written under the [MIT] license.

[MIT]: /LICENSE
