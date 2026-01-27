import discord
import parser
import matchups
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.command()
async def matchup(ctx):
    content = ctx.message.content.replace("!matchup", "").strip()
    leaders = content.split(",")
    parsed_leaders = [parser.parse_leader(leader.strip()) for leader in leaders]
    flattened_leaders = [item for sublist in parsed_leaders for item in sublist]
    if flattened_leaders:
        matches = matchups.fetch_matchups(flattened_leaders)
        if matches:
            response_embeds = matchups.format_matchup_response(matches)
            for embed in response_embeds:
                await ctx.send(embed=embed)
        else:
            await ctx.send("No matchups found")
    else:
        await ctx.send(f"No leaders found for '{flattened_leaders}'.")


# hardcoded during dev, token will be reset and made into env for deploy
bot.run("MTQ2NTczOTExOTIxNTkwMzAwNg.GuNH1I.kqcSRS-ZT_XCNHwKKO5BViJbme8b2lL2x5vq10")
