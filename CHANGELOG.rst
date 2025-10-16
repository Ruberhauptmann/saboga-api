
.. _changelog-0.0.58:

0.0.58 — 2025-10-16
-------------------

Changed
^^^^^^^

- Scale node sizes logarithmically

Fixed
^^^^^

- Construct boardgame graph when scraping

.. _changelog-0.0.54:

0.0.54 — 2025-10-15
-------------------

Changed
^^^^^^^

- Switched DB to Postgres

.. _changelog-0.0.53:

0.0.53 — 2025-09-14
-------------------

Fixed
^^^^^

- Catch timeout errors in scraper

.. _changelog-0.0.52:

0.0.52 — 2025-09-14
-------------------

Fixed
^^^^^

- Scraper with new backlink field for boardgames

.. _changelog-0.0.51:

0.0.51 — 2025-09-14
-------------------

Added
^^^^^

- Cluster boardgames by categories, designers, families, mechanics

- Cluster categories, designers, families, mechanics connected by boardgames (similar to designers)

Changed
^^^^^^^

- Endpoints for categories, designers, mechanics, families with pagination

.. _changelog-0.0.50:

0.0.50 — 2025-08-28
-------------------

Changed
^^^^^^^

- Better layout for designer network graph

- Endpoints for categories, designers, families, mechanics also return linked boardgames

- Search function now searches across categories, designers, families and mechanics as well

.. _changelog-0.0.47:

0.0.47 — 2025-08-23
-------------------

Added
^^^^^

- Endpoints for categories, mechanics, families

Changed
^^^^^^^

- Save designer network graph in database for faster API calls

- Cluster the designers in the network graph

- Better calculation of trends

.. _changelog-0.0.46:

0.0.46 — 2025-08-17
-------------------

Fixed
^^^^^

- Some bugs in metadata scraper

.. _changelog-0.0.45:

0.0.45 — 2025-08-17
-------------------

Added
^^^^^

- Scraper that fills in the metadata for games (designers, categories, images, etc.)

.. _changelog-0.0.44:

0.0.44 — 2025-08-16
-------------------

Changed
^^^^^^^

- Layout of designer network graph for Sigma.js

Fixed
^^^^^

- Bug in trending games when designer links were not fetched

.. _changelog-0.0.43:

0.0.43 — 2025-08-16
-------------------

Added
^^^^^

- Calculate volatility across rank history (std / mean)

- Endpoint for network analysis of boardgame designers

- Endpoint for trending games

Changed
^^^^^^^

- More extensive logging

Fixed
^^^^^

- Show the date entries in the yearly and weekly filter starting from the newest date

.. _changelog-0.0.42:

0.0.42 — 2025-07-06
-------------------

Changed
^^^^^^^

- Scraper now uses the Boardgamegeek data dump to update the rank history

.. _changelog-0.0.41:

0.0.41 — 2025-06-23
-------------------

Fixed
^^^^^

- Fixed bug in scraper where the wrong variable was read out from the config

.. _changelog-0.0.40:

0.0.40 — 2025-06-17
-------------------

Fixed
^^^^^

- Bug in getting the time series information for the rank charts, now the information from the correct dates are chosen

- Remove NaN values before applying prediction for ranks and ratings

- Add name to data in scraper

.. _changelog-0.0.39:

0.0.39 — 2025-04-07
-------------------

Changed
^^^^^^^

- Save names and rank information when uploading the boardgamegeek data dump

- Return only date when returning rank_history

- Save a rank_history entry when uploading a data dump from BGG

Fixed
^^^^^

- Upload of boardgamegeek data dumps

- Calculation of rank changes in the right direction

- Scrape only historic rank data before the last date that is in the database

.. _changelog-0.0.38:

0.0.38 — 2025-04-04
-------------------

Changed
^^^^^^^

- Unified exceptions

Fixed
^^^^^

- Pagination started at one page later than it is supposed to

- Data from a single game returned correctly with new time series

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
