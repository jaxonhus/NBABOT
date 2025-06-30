import discord
from discord.ext import commands
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import pandas as pd
import os

pd.set_option('display.max_columns', 500)

# Existing NBA stats functions
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
        games = row['GP']
        if games == 0:
            continue
        team = row ['TEAM_ABBREVIATION']
        year = row['SEASON_ID' + 1]
        ppg = row['PTS'] / games
        rpg = row['REB'] / games
        apg = row['AST'] / games
        bpg = row['BLK'] / games
        spg = row['STL'] / games
        tovpg = row['TOV'] / games
        pfpg = row['PF'] / games
        fgmpg = row['FGM'] / games
        fg3mpg = row['FG3M'] / games
        fg_pct = row['FG_PCT']
        f3g_pct = row['F3G_PCT']
        ft_pct = row['FT_PCT']

        stats_strings.append(
            f"{team}, {seasonId}: PPG {ppg}, RPG {rpg}, APG {apg}, BPG {bpg}, SPG {spg}, TO {tovpg}, PF {pfpg}"
        )

    full_stats = "\n".join(stats_strings)
    return full_stats, None

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# !commands
@bot.command()
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

# !playerstats command
@bot.command(name='playerstats')
async def playerstats(ctx, *, player_name: str):
    await ctx.send(f"Fetching stats for {player_name}...")
    stats, error = get_player_career_stats(player_name)
    if error:
        await ctx.send(error)
        return
    
    # Character limit
    if len(stats) > 1900:
        stats_chunks = [stats[i:i+1900] for i in range(0, len(stats), 1900)]
        for chunk in stats_chunks:
            await ctx.send(f"```{chunk}```")
    else:
        await ctx.send(f"```{stats}```")

#!teamstats
        
#!compare
        
#!leagueleaders

#!alltimeleaders
        
token = os.getenv('DISCORD_TOKEN') 
bot.run(token)
