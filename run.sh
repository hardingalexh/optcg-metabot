#!/bin/bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR" || exit 1

uv run src/scrapers/scraper.py >> ./logs/scraper.log 2>&1 &
uv run src/bot/discord_bot.py >> ./logs/discord_bot.log 2>&1 &

wait