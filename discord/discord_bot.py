import discord
import parser
import matchups as mu
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def command_func(ctx):
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


# hardcoded during dev, token will be reset and made into env for deploy
bot.run("MTQ2NTczOTExOTIxNTkwMzAwNg.GuNH1I.kqcSRS-ZT_XCNHwKKO5BViJbme8b2lL2x5vq10")
