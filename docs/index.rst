.. discord-ws documentation master file, created by
   sphinx-quickstart on Fri Dec  1 09:37:57 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to discord-ws's documentation!
======================================

``discord-ws`` is a minimal, asynchronous Python wrapper for the Discord Gateway API.

.. note::

   This library is **not** associated with `discord-ws <https://pypi.org/project/discord-ws/>`_
   on PyPI, which is written by a different author.
   For now, there are no plans to release this package on PyPI.

Features
--------

- Fully implements Discord's `connection lifecycle`_
- Allows receiving JSON-encoded payloads (not ETF)
- Can switch between plain text and `zlib transport compression`_
- Provides access to raw dispatch events via callback mechanism

.. _connection lifecycle: https://discord.com/developers/docs/topics/gateway#connections
.. _zlib transport compression: https://discord.com/developers/docs/topics/gateway#encoding-and-compression

Usage
-----

Assuming you have Python 3.11+ and Git installed, you can install this library with:

.. code-block:: shell

   pip install git+https://github.com/thegamecracks/discord-ws

If you want to test out the library without writing a script, create a bot on
Discord's `Developer Portal`_, copy your bot token, and try out the built-in CLI:

.. code-block:: shell

   python -m discord_ws --standard-intents --zlib-stream

If you do want to write a script, import the library and use the
:py:class:`~discord_ws.Client` class to establish a connection yourself:

.. code-block:: python

   import asyncio
   import discord_ws

   client = discord_ws.Client(
       token="Bot YOUR_TOKEN_HERE",
       intents=discord_ws.Intents.standard(),
   )

   @client.on_dispatch
   async def handle_event(event: discord_ws.DispatchEvent):
       ...  # Do something with the events received from Discord

   asyncio.run(client.run())

.. _Developer Portal: https://discord.com/developers/applications
.. _Client: https://github.com/thegamecracks/discord-ws/blob/main/src/discord_ws/client/client.py

Resources
---------

- GitHub Repository: https://github.com/thegamecracks/discord-ws
- Discord Docs: https://discord.com/developers/docs/topics/gateway

License
-------

This project is written under the MIT license.

Client API Reference
--------------------

.. autoclass:: discord_ws.Client

   .. autoclasstoc::

.. autoclass:: discord_ws.DispatchEvent
   :undoc-members:

Gateway Intents
---------------

.. autoclass:: discord_ws.Intents

Exceptions
----------

.. autoclass:: discord_ws.AuthenticationFailedError
.. autoclass:: discord_ws.ClientError
.. autoclass:: discord_ws.ConnectionClosedError
.. autoclass:: discord_ws.GatewayInterrupt
.. autoclass:: discord_ws.GatewayReconnect
.. autoclass:: discord_ws.HeartbeatLostError
.. autoclass:: discord_ws.PrivilegedIntentsError
.. autoclass:: discord_ws.SessionInvalidated
