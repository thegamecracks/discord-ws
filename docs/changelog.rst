Changelog
=========

v0.5.0
------

Full Changelog: https://github.com/thegamecracks/discord-ws/compare/v0.4.0...v0.5.0

Fixes
^^^^^

- Fix py.typed marker not being included in the package
- Use ``if __name__ == "__main__":`` condition in ``discord_ws/__main__.py``
  to prevent side effects when imported

Documentation
^^^^^^^^^^^^^

- Add this documentation site

  If you found me from the repository, 👋 hello!

v0.4.0
------

Full Changelog: https://github.com/thegamecracks/discord-ws/compare/v0.3.0...v0.4.0

Breaking Changes
^^^^^^^^^^^^^^^^

- Significantly refactor :py:class:`~discord_ws.Client` internal methods
  for improved extensibility
- :py:meth:`Client.run(reconnect=False) <discord_ws.Client.run>`
  may now raise :py:exc:`~discord_ws.GatewayReconnect`
  and :py:exc:`~discord_ws.SessionInvalidated`
- :py:meth:`Client.run() <discord_ws.Client.run>` is now expected to raise an exception group
- Remove ``Heart(client)`` dependency in favour of
  directly accepting a stream in ``Heart.stay_alive()``
- Remove client attribute from ``Stream`` protocol in favour of ``ws`` interface

New Features
^^^^^^^^^^^^

- Add :py:attr:`Client.presence <discord_ws.Client.presence>`
  and :py:meth:`Client.set_presence() <discord_ws.Client.set_presence>`
  for setting bot presence
- Add :py:attr:`Client.large_threshold <discord_ws.Client.large_threshold>`
  to specify the desired threshold for offline members to not be sent

Fixes
^^^^^

- Correct typo causing :py:attr:`~discord_ws.DispatchEvent.seq` to be missing when sending RESUME event

v0.3.0
------

Full Changelog: https://github.com/thegamecracks/discord-ws/compare/v0.2.0...v0.3.0

Breaking Changes
^^^^^^^^^^^^^^^^

- Potentially raise :py:exc:`~discord_ws.HeartbeatLostError`
  when using :py:meth:`Client.run(reconnect=False) <discord_ws.Client.run>`
  rather than cleanly exiting
- Remove :py:meth:`Client.create() <discord_ws.Client.create>` classmethod
  in favour of constructing :py:class:`~discord_ws.Client` directly
- Replace ``on_dispatch`` parameter from :py:class:`~discord_ws.Client()`
  with :py:meth:`Client.on_dispatch() <discord_ws.Client.on_dispatch>` method

Fixes
^^^^^

- Prevent potential race condition with session ID being unset
- Use local :py:class:`Random <random.Random>` instance in heartbeat to avoid
  affecting user state

v0.2.0
------

Full Changelog: https://github.com/thegamecracks/discord-ws/compare/v0.1.0...v0.2.0

New Features
^^^^^^^^^^^^

- Improve logging of connection closures
- Implement exponential backoff to avoid spamming Discord with connections

Fixes
^^^^^

- Prevent full write buffer from causing double heartbeats
- Fix client reconnecting after calling :py:meth:`Client.close() <discord_ws.Client.close>`

Documentation
^^^^^^^^^^^^^

- Indicate that bot tokens should be prefixed with ``Bot``

v0.1.0
------

This marks the first release of the discord-ws library! 🎉

.. code-block:: ruby
   :force:

   $ python -m discord_ws --env-token TOKEN --no-intents
         discord_ws.client.client (   DEBUG) => Requesting gateway URL
         discord_ws.client.client (   DEBUG) => Starting connection loop
         discord_ws.client.client (   DEBUG) => Creating websocket connection
         discord_ws.client.stream (   DEBUG) => Received 124 chars
         discord_ws.client.client (   DEBUG) => Received hello from gateway
      discord_ws.client.heartbeat (   DEBUG) => Waiting 42.17s for heartbeat
         discord_ws.client.client (   DEBUG) => Sending identify payload
         discord_ws.client.stream (   DEBUG) => Received 1855 chars
         discord_ws.client.client (   DEBUG) => Received READY event
