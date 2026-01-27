#!/bin/bash

python data/scraper.py >> ./logs/scraper.log 2>&1 &
python discord/discord_bot.py >> ./logs/discord_bot.log 2>&1 &

wait