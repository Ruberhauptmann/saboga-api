
.. _changelog-0.0.14:

0.0.14 — 2024-07-18
-------------------

Changed
^^^^^^^

- Removed everything, only boardgames overview with connection to BoardGameGeek

.. _changelog-0.0.13:

0.0.13 — 2024-07-06
-------------------

Changed
^^^^^^^

- Auth system with cookies for frontend

.. _changelog-0.0.12:

0.0.12 — 2024-06-30
-------------------

Changed
^^^^^^^

- Ability to create results for plays

Security
^^^^^^^^

- Fix reading of secret token from environment variable

.. _changelog-0.0.11:

0.0.11 — 2024-06-28
-------------------

Added
^^^^^

- Add account creation and login via fastapi-users

- Collections of games to user accounts

- Interface to read all collections

Changed
^^^^^^^

- Moved plays into user accounts

- Add results

.. _changelog-0.0.8:

0.0.8 — 2024-05-15
------------------

Changed
^^^^^^^

- Switched to MongoBD via Beanie as database backend

.. _changelog-0.0.7:

0.0.7 — 2024-04-07
------------------

Added
^^^^^

- Endpoint to link a play onto a game

Changed
^^^^^^^

- Expanded FastAPI models, set some fields nullable
- Versioning for Docker containers

.. _changelog-0.0.6:

0.0.6 — 2024-04-06
------------------

Added
^^^^^

- Routes to add, edit and delete games

- Routes to add, edit and delete play sessions

Changed
^^^^^^^

- Full database and FastAPI models with relationships
