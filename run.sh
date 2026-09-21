#!/bin/bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR" || exit 1

uv run --directory "$ROOT_DIR" python -m scrapers.scraper >> ./logs/scraper.log 2>&1 &
uv run --directory "$ROOT_DIR" python -m bot.discord_bot >> ./logs/discord_bot.log 2>&1 &

wait