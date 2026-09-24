# OPTCG-Metabot

This bot runs for the Cross Guild server, providing matchup data when asked.

## Data Layer

The data scraper(s) are located in the `/data` directory, and pull leaders from limitlesstcg.com and matchups from tcgmatchmaking.com.

## Discord bot

The Discord bot is located in `src/bot`.

## Dev Setup
This application leverages `uv` for managing environments, dependencies, and run scripts. Install `uv` with the [method of your choosing](https://docs.astral.sh/uv/getting-started/installation/).

1. Create a [Discord App](https://docs.discord.com/developers/quick-start/getting-started) and copy the application token into a new `.env` file based on `.env.example`.
2. Install dependencies with `uv` by running `uv sync`.


## Features

### Data Scrapers
The `src/scrapers` directory contains the following scripts which populate data in the `/data` directory.
1. `leaders.py`: run this file (`uv run src/scrapers/leaders.py`) to create a `leaders.json` file that includes metadata for all leaders as well as download all leader card images for use in the `meta` feature.
2. `stats.py`: run this file (`uv run src/scrapers/stats.py`) to create a number of files:
    1. `meta_X.csv` files for the individual meta reports: `1b`, `2b`, `all`, and `eastern`.
    2. `out_X.csv` files for the indivdual matchup reports: `1b`, `2b`, `all`, `eastern`, and archived metas from `OP08` to present

    *__Note__: this file requires a valid `leaders.json` file to run.*
3. `scraper.py`: run this file (`uv run src/scrapers/scraper.py`) to run a scheduled task that, at startup and every night at midnight (using the [schedule package](https://schedule.readthedocs.io/en/stable/)), cleans the contents of the `/tmp` directory, runs `leaders.py` and `stats.py`.

### Discord Bot
You can make the discord bot available by running `uv run src/bot/discord_bot.py`. This turns the bot on with the following features:
1. `!matchup`: Users can say `!matchup <leader>` to see the top 10 matchups (by representation) for a given leader. They can also see a specfic matchup by saying `!matchup <leader>, <opponent>`. Syntax for leaders allows for users to choose either a set (formatted as `OP-01`, `OP01`, or `01`), or a color (formatted as `Black` or `B`, accepting dual colors, and using `U` for blue).
2. `!meta`: The `!meta` feature generates a chart for the top 20 leaders showing their representation in the data (as standard deviations from the mean games played) and their total winrate. `!meta <leader>` will show the top 20 matchups for a given leader, using the same syntax as the `!matchup` feature.
3. `!market`: Users can ask `!market <card>` (set number required) to see the trends in marketplace transactions for a given card. Note that this will provide it for all treatments of a given card (as in base, alt, SP, etc).

## Deployment
The `run.sh` bash script runs both the scraper and discord bot as background tasks with logging. To build and deploy the docker image:

1. `docker build . -t buggy-bot`
2. `docker run -d --restart always buggy-bot`
