
.. _changelog-0.0.20:

0.0.20 — 2024-07-23
-------------------

Changed
^^^^^^^

- Added attribution to Boardgamegeek in the API documentation

- Boardgame schema now includes rank change

Fixed
^^^^^

- Return correct links in the link header

- Error in the scraper that caused skipping of a lot of ids

.. _changelog-0.0.19:

0.0.19 — 2024-07-23
-------------------

Changed
^^^^^^^

- Single boardgame route now takes the Boardgamegeek ID

- Boardgame list view can now display historical data

- Boardgame schema now includes rating change

Fixed
^^^^^

- A bug in the scraper that caused shut it down when the first scrape did not get an answer at first

.. _changelog-0.0.15:

0.0.15 — 2024-07-21
-------------------

Added
^^^^^

- Scraper script to regularly get all game data

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
