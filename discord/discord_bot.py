import os
import datetime

from dotenv import load_dotenv
import discord
import parser
import matchups as mu
from discord.ext import commands
import re

# Load environment variables from .env file
load_dotenv()

# set up discord bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOURNAMENT_MODE = False


async def command_func(ctx):
    """parses the matchup command

    Args:
        ctx (): The context object from discord
    """
    print(
        f"{datetime.datetime.now().isoformat()}: {ctx.author.name} searched {ctx.message.content}"
    )
    if not TOURNAMENT_MODE:
        content = ctx.message.content.replace(f"!{ctx.invoked_with}", "").strip()
        prefix = "all"
        match = re.search(r"\((.*?)\)", content)
        if match:
            prefix = match.group(1)
            content = re.sub(r"\(.*?\)", "", content).strip()
        leaders = content.split(",")
        parsed_leaders = parser.parse_leader(leaders[0].strip())
        if len(leaders) > 1:
            parsed_opponents = parser.parse_leader(leaders[1].strip())
        if len(leaders) == 1:
            matches = mu.fetch_matchups(parsed_leaders, prefix=prefix)
        if len(leaders) > 1:
            matches = mu.fetch_matchups(parsed_leaders, parsed_opponents, prefix=prefix)
        response_embeds = mu.format_matchup_response(matches)

        if not response_embeds:
            await ctx.send("No matchups found")
        elif len(response_embeds) <= 10:
            for embed in response_embeds:
                await ctx.send(embed=embed)
        else:
            await ctx.send(
                f"Found {len(response_embeds)} matchups. Please refine your search to get fewer results."
            )
    else:
        # tournament mode enabled
        print(f"{ctx.author.name} searched in tournament mode")
        await ctx.send(
            "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExdmNiOTUzZzhxZWg1NmxuMHdmbzUwNXFseGp6ZzVyY2s1c3lnd2psNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/V6e0kch9OgUbph9jBB/giphy.gif"
        )
        await ctx.send("_No cheating in tournament mode!_ :clown:")


@bot.command()
async def matchups(ctx):
    await command_func(ctx)


@bot.command()
async def matchup(ctx):
    await command_func(ctx)


# Load Discord token from environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")

bot.run(DISCORD_TOKEN)
