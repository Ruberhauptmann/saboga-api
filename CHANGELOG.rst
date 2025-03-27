
.. _changelog-0.0.36:

0.0.36 — 2025-03-27
-------------------

Changed
^^^^^^^

- Forecast also includes predictions for ratings

Fixed
^^^^^

- Removed '/' after root paths (e.g. /boardgames instead of /boardgames/)

- Fix forecast route

.. _changelog-0.0.35:

0.0.35 — 2025-03-24
-------------------

Added
^^^^^

- Prediction of future rank data

- Placeholders for remaining routes

- Simple search function for boardgames

- Scraper to get full historical ranking data

Changed
^^^^^^^

- Expose metric with the number of boardgames that dont have a rank

- Scrape more data

Fixed
^^^^^

- API response for the boardgame overview returns changes in ranks and ratings between the correct dates

.. _changelog-0.0.34:

0.0.34 — 2025-03-23
-------------------

Added
^^^^^

- Logger that sends to a loki instance

Fixed
^^^^^

- Fix error in csv upload, added a lot of things that were not ranked

.. _changelog-0.0.33:

0.0.33 — 2025-03-22
-------------------

Added
^^^^^

- Prometheus for exporting metrics

.. _changelog-0.0.32:

0.0.32 — 2025-03-22
-------------------

Added
^^^^^

- Return historical data for a single game

Changed
^^^^^^^

- Scrape images and create thumbnail versions

- Only save scraped game when last save was more than one day old


.. _changelog-0.0.30:

0.0.30 — 2024-12-07
-------------------

Changed
^^^^^^^

- Boardgame overview route now returns historical data as a comparison between two dates

Fixed
^^^^^

- Fix default date argument in boardgame list

.. _changelog-0.0.27:

0.0.27 — 2024-08-07
-------------------

Changed
^^^^^^^

- Refactor update scraper

.. _changelog-0.0.24:

0.0.24 — 2024-08-05
-------------------

Fixed
^^^^^

- Error in scraper that caused failure when rank or rating is None

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
