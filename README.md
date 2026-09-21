# OPTCG-Metabot

This bot runs for the Cross Guild server, providing matchup data when asked.

## Data Layer

The data scraper(s) are located in the `/data` directory, and pull leaders from limitlesstcg.com and matchups from tcgmatchmaking.com.

## Discord bot

The Discord bot is located in `src/bot`.

## Dev Setup

1. Create an env file based on the example provided, and provide a discord app token.
2. Install dependencies as listed in the requirements.txt file
3. Run `uv run python -m scrapers.scraper` to run the scraper.
4. Run `uv run python -m bot.discord_bot` to run the Discord bot.

## Deployment

The `run.sh` bash script runs both the scraper and discord bot as background tasks with logging. To build and deploy the docker image:

1. `docker build . -t buggy-bot`
2. `docker run -d --restart always buggy-bot`
