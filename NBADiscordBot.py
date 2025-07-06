import discord
from discord.ext import commands
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import pandas as pd
import os
from dotenv import load_dotenv


pd.set_option('display.max_columns', 500)

load_dotenv()

def get_player_id(player_name):
    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        return None
    return player_dict[0]['id']

def get_player_career_stats(player_name):
    player_id = get_player_id(player_name)
    if not player_id:
        return None, f"Could not find player: {player_name}"

    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    df = career.get_data_frames()[0]

    # Collect stats strings per season
    stats_strings = []
    for index, row in df.iterrows():
        seasonId = row['SEASON_ID']
        team_abbr = row['TEAM_ABBREVIATION']
        games = row['GP']
        if games == 0:
            continue
        ppg = round(row['PTS'] / games, 1)
        rpg = round(row['REB'] / games, 1)
        apg = round(row['AST'] / games, 1)
        bpg = round(row['BLK'] / games, 1)
        spg = round(row['STL'] / games, 1)
        tovpg = round(row['TOV'] / games, 1)
        pfpg = round(row['PF'] / games, 1)
        fgmpg = round(row['FGM'] / games, 1)
        fg3mpg = round(row['FG3M'] / games, 1)

        stats_strings.append(
            f"{team_abbr} {seasonId}: PPG {ppg}, RPG {rpg}, APG {apg}, BPG {bpg}, SPG {spg}, TO {tovpg}, PF {pfpg}, 3PM {fg3mpg}"
        )

    # Join all seasons stats in one string with line breaks
    full_stats = "\n".join(stats_strings)
    return full_stats, None


# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# !hi
@bot.command(name = 'hi')
async def hi(ctx):
    hi_text = (
        f"Hello {ctx.author}!"
    )
    await ctx.send(hi_text)

# !commands
@bot.command(name = 'commands')
async def commands(ctx):
    help_text = (
        "```"
        "Here's a list of commands:\n\n"
        "!commands       - Show a list of all commands\n"
        "!playerstats    - Show stats for a specific player. Format: !playerstats Anthony Edwards 2024\n"
        "!teamstats      - Show stats for a specific team.   Format: !teamstats Timberwolves 2020\n"
        "!compare        - Compare 2 separate players' stats. Format: !compare Anthony Edwards, LeBron James 2022\n"
        "!leagueleaders  - Show the league's top 10 leaders in a stat. Format: !leagueleaders Assists 2025\n"
        "!alltimeleaders - Show the all-time leaders for a stat. Format: !alltimeleaders Points"
        "```"
        "\n**Note:** If no year is added, the default will be career-based."
    )
    await ctx.send(help_text)

# !playerstats
@bot.command(name='playerstats')
async def playerstats(ctx, *, player_name: str):
    await ctx.send(f"Fetching stats for {player_name}...")
    stats, error = get_player_career_stats(player_name)
    if error:
        await ctx.send(error)
        return

    # Discord message limit is 2000 chars, so split if too long
    if len(stats) > 1900:
        stats_chunks = [stats[i:i+1900] for i in range(0, len(stats), 1900)]
        for chunk in stats_chunks:
            await ctx.send(f"```{chunk}```")
    else:
        await ctx.send(f"```{stats}```")

# !teamstats
'''
@bot.command(name = 'teamstats')
async def teamstats(ctx, *, team_name: str):
    await ctx.send(f"Fetching stats for the {team_name}")
    stats, error = get_team_stats(team_name)
    if error:
        await ctx.send(error)
        return
''' 
# !compare
    #test
# !leagueleaders
    
# !alltimeleaders

# Run the bot with your Discord bot token
token = os.getenv('DISCORD_TOKEN')  # Make sure to set your token in environment variables
bot.run(token)