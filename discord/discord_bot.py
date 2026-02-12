import os
from dotenv import load_dotenv
import discord
import parser
import matchups as mu
from discord.ext import commands

# Load environment variables from .env file
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def command_func(ctx):
    content = ctx.message.content.replace("!matchups", "").strip()
    content = ctx.message.content.replace("!matchup", "").strip()
    leaders = content.split(",")
    parsed_leaders = parser.parse_leader(leaders[0].strip())
    if len(leaders) > 1:
        parsed_opponents = parser.parse_leader(leaders[1].strip())
    if len(leaders) == 1:
        matches = mu.fetch_matchups(parsed_leaders)
    if len(leaders) > 1:
        matches = mu.fetch_matchups(parsed_leaders, parsed_opponents)
    if matches:
        response_embeds = mu.format_matchup_response(matches)
        for embed in response_embeds:
            await ctx.send(embed=embed)
    else:
        await ctx.send("No matchups found")


@bot.command()
async def matchup(ctx):
    await command_func(ctx)


@bot.command()
async def matchups(ctx):
    await command_func(ctx)


# Load Discord token from environment
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not found in .env file")

bot.run(DISCORD_TOKEN)
