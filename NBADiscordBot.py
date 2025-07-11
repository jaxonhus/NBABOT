import discord
import pandas as pd
import os
import re
from discord.ext import commands
from nba_api.stats.static import players
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints import teamyearbyyearstats
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.endpoints import alltimeleadersgrids
from dotenv import load_dotenv


pd.set_option('display.max_columns', 500)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')


def get_player_id(player_name):
    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        return None
    return player_dict[0]['id']

def get_player_career_stats(player_name, season = None):
    player_id = get_player_id(player_name)
    if not player_id:
        return None, f"Could not find {player_name}"

    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    df = career.get_data_frames()[0]
    df = df.sort_values(by='SEASON_ID')

    if season:
        if not re.match(r"^\d{4}$", season):
            return None, f"Invalid season format: {season}. Expected 4-digit year like 2025."
        season_id = f"{int(season)-1}-{str(season)[-2:]}"
        df = df[df['YEAR'] == season_id]

        if df.empty and season:
            return None, f"Could not find stats for {player_name} in {season}."
    else:
        return None
            
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

def get_team_id(team_name):
    team_dict = teams.find_teams_by_nickname(team_name)
    if not team_dict:
        return None
    return team_dict[0]['id']

def get_team_stats(team_name, season = None):
    team_id = get_team_id(team_name)
    if not team_id:
        return None, f"Could not find the {team_name}, format: !teamstats Lakers 2025"
    
    career = teamyearbyyearstats.TeamYearByYearStats(team_id=team_id)
    df = career.get_data_frames()[0]
    df = df.sort_values(by='YEAR')

    if season:
        if not re.match(r"^\d{4}$", season):
            return None, f"Invalid season format: {season}. Expected 4-digit year like 2025."
        season_id = f"{int(season)-1}-{str(season)[-2:]}"
        df = df[df['YEAR'] == season_id]

        if df.empty:
            return None, f"Could not find stats for {team_name} in {season}."
    else:
        return None, f"Please specify a season year like 2025."

    stats_strings = []
    for index, row in df.iterrows():
        team_id = row['TEAM_ID']
        team_city = row['TEAM_CITY']
        games = row['GP']
        year = row['YEAR']
        wins = row['WINS']
        losses = row['LOSSES']
        win_pct = row['WIN_PCT']
        po_wins = row['PO_WINS']
        po_losses = row['PO_LOSSES']
        finals_app = row['NBA_FINALS_APPEARANCE']
        ppg = round(row['PTS'] / games, 1)
        rpg = round(row['REB'] / games, 1)
        apg = round(row['AST'] / games, 1)

        if po_losses == 0 and po_wins == 0:
            stats_strings.append(
            f"{team_city} {year}: {wins}-{losses} ({win_pct*100:.1f}% win), "
            f"PPG {ppg}, APG {apg}, RPG {rpg}, Did not make the Playoffs"
        )
        elif po_wins < 4:
            stats_strings.append(
            f"{team_city} {year}: {wins}-{losses} ({win_pct*100:.1f}% win), "
            f"PPG {ppg}, APG {apg}, RPG {rpg}, Playoffs W-L: {po_wins}-{po_losses}, Eliminated in the First Round"
        )
        elif po_wins < 8:
            stats_strings.append(
            f"{team_city} {year}: {wins}-{losses} ({win_pct*100:.1f}% win), "
            f"PPG {ppg}, APG {apg}, RPG {rpg}, Playoffs W-L: {po_wins}-{po_losses}, Eliminated in the Second Round"
        )
        elif po_wins < 12:
            stats_strings.append(
            f"{team_city} {year}: {wins}-{losses} ({win_pct*100:.1f}% win), "
            f"PPG {ppg}, APG {apg}, RPG {rpg}, Playoffs W-L: {po_wins}-{po_losses}, Eliminated in the Conference Finals"
        )
        else: 
            stats_strings.append(
            f"{team_city} {year}: {wins}-{losses} ({win_pct*100:.1f}% win), "
            f"PPG {ppg}, APG {apg}, RPG {rpg}, Playoffs W-L: {po_wins}-{po_losses}, Made the Finals"
        )
            
    full_stats = "\n".join(stats_strings)
    return full_stats, None
    
def season_to_year(season: str) -> str:
    if not re.match(r"\d{4}", season):
        return None
    short_year = season[-2:]
    yy = int(short_year)
    if yy < 40:
        century = 2000
    else: century = 1900
    full_year = century + yy
    return str(full_year)


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
        "!playerstats    - Show stats for a specific player. Format: !playerstats Anthony Edwards 2025\n"
        "!teamstats      - Show stats for a specific team.   Format: !teamstats Timberwolves 2025\n"
        "!teamroster     - Show the roster for a team. Format: !teamroster Lakers 2025"
        "!compare        - Compare 2 separate players' stats. Format: !compare Michael Jordan, LeBron James\n"
        "!leagueleaders  - Show the league's top 10 leaders in a stat. Format: !leagueleaders Assists 2025\n"
        "!alltimeleaders - Show the all-time leaders for a stat. Format: !alltimeleaders Points"
        "```"
        "\n**Note:** If no year is added, the default will be career-based."
    )
    await ctx.send(help_text)

#use re.match to take the last 2 digits of the year row in the data, add "20" + shortened year if under 40. If over 40, add "19". somehow combine those two digits and match them in the user input year to correlate the year

# !playerstats
@bot.command(name='playerstats')
async def playerstats(ctx, *, args: str):
    parts = args.rsplit(maxsplit=1)
    if re.match(r"\d{4}", parts[-1]):
        player_name = parts[0]
        season = parts[-1]
    else:
        player_name = args 
        season = None

    if season:
        await ctx.send(f"Getting stats for {player_name} in {season}")
    else:
        await ctx.send(f"Getting career stats for {player_name}")

    stats, error = get_player_career_stats(player_name, season)

    if error:
        await ctx.send(error)
        return
    
    if len(stats) > 1900:
        stats_chunks = [stats[i:i+1900] for i in range(0, len(stats), 1900)]
        for chunk in stats_chunks:
            await ctx.send(f"```{chunk}```")
    else:
        await ctx.send(f"```{stats}```")

# !teamstats
@bot.command(name = 'teamstats')
async def teamstats(ctx, *, args: str):
    parts = args.rsplit(maxsplit=1)
    if re.match(r"\d{4}", parts[-1]):
        team_name = parts[0]
        season = parts[-1]
    else:
        team_name = args 
        season = None, f"Invalid Season"

    if season:
        await ctx.send(f"Getting stats for {team_name} in {season}")
    else:
        await ctx.send(f"Please input a season. Format: !teamstats {team_name} 2025")

    stats, error = get_team_stats(team_name, season)

    if error: 
        await ctx.send(error)
        return

    if len(stats) > 1900:
        stats_chunks = [stats[i:i+1900] for i in range(0, len(stats), 1900)]
        for chunk in stats_chunks:
            await ctx.send(f"```{chunk}```")
    else:
        await ctx.send(f"```{stats}```")

# !teamroster

# !compare

# !leagueleaders
        
# !alltimeleaders

# Run the bot with your Discord bot token
print
if token:
    bot.run(token)
else: 
    print("Could not find token")
