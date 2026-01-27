# OPTCG-Metabot

This bot runs for the Cross Guild server, providing matchup data when asked.

## Data Layer

The data scraper(s) are located in the `/data` directory, and pull leaders from limitlesstcg.com and matchups from tcgmatchmaking.com.

## Discord bot

The Discord bot is located in the `/discord` directory.

## Dev Setup

1. Create an env file based on the example provided, and provide a discord app token.
2. Install dependencies as listed in the requirements.txt file
3. Run `python data/scraper.py` to run the scraper, which will run the leaders/data scraper.
4. Run `python discord/discord_bot.py` to run the discord bot

## Deployment

The `run.sh` bash script runs both the scraper and discord bot as background tasks with logging. To build and deploy the docker image:

1. `docker build . -t buggy-bot`
2. `docker run -d buggy-bot --restart always`
