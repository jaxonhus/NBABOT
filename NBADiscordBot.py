import discord
from discord.ext import commands
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import pandas as pd
import os
from dotenv import load_dotenv


pd.set_option('display.max_columns', 500)

load_dotenv()

# Your existing NBA stats functions
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
        ppg = row['PTS']
        rpg = row['REB']
        apg = row['AST']
        bpg = row['BLK']
        spg = row['STL']
        tovpg = row['TOV']
        pfpg = row['PF']
        fgmpg = row['FGM']
        fg3mpg = row['FG3M']

        stats_strings.append(
            f"{seasonId}: PPG {ppg}, RPG {rpg}, APG {apg}, BPG {bpg}, SPG {spg}, TO {tovpg}, PF {pfpg}, 3PM {fg3mpg}"
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

# !playerstats command
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

# Run the bot with your Discord bot token
token = os.getenv('DISCORD_TOKEN')  # Make sure to set your token in environment variables
bot.run(token)
