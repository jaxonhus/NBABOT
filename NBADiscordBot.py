import discord
import pandas as pd
import os
import re
import csv
from discord.ext import commands
from nba_api.stats.static import *
from nba_api.stats.endpoints import *
from dotenv import load_dotenv


pd.set_option('display.max_columns', 500)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')


def get_player_id(player_name):
    player_dict = players.find_players_by_full_name(player_name)
    if not player_dict:
        return None
    return player_dict[0]['id']

def season_to_year(season: str) -> str:
    if not re.match(r"^\d{4}$", season):
        return None
    full_year = int(season)
    start_year = full_year - 1
    end_year_short = str(full_year)[-2:]
    return f"{start_year}-{end_year_short}"

def get_player_career_stats(player_name, season = None):
    player_id = get_player_id(player_name)
    if not player_id:
        return None, f"Could not find {player_name}"

    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    df = career.get_data_frames()[0]
    df = df.sort_values(by='SEASON_ID')

    if season:
        season = season_to_year(season)
        df = df[df['SEASON_ID'] == season]
        if df.empty:
            return None, f"Could not find stats for {player_name} in {season}. Format: !playerstats Lebron James 2025"

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
            f"{team_abbr} {seasonId}: GP: {games}, PPG: {ppg}, RPG: {rpg}, APG: {apg}, BPG: {bpg}, SPG: {spg}, TO: {tovpg}, PF: {pfpg}, FGM: {fgmpg} 3PM: {fg3mpg}"
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
        season = season_to_year(season)
        df = df[df['YEAR'] == season]
        if df.empty:
            return None, f"Could not find stats for {team_name} in {season}. Format: !teamstats Lakers 2025"

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
        elif po_wins < 16:
            stats_strings.append(
            f"{team_city} {year}: {wins}-{losses} ({win_pct*100:.1f}% win), "
            f"PPG {ppg}, APG {apg}, RPG {rpg}, Playoffs W-L: {po_wins}-{po_losses}, Lost in the Finals"
        )
        else:
            stats_strings.append(
            f"{team_city} {year}: {wins}-{losses} ({win_pct*100:.1f}% win), "
            f"PPG {ppg}, APG {apg}, RPG {rpg}, Playoffs W-L: {po_wins}-{po_losses}, Won the Championship!"
        )

    full_stats = "\n".join(stats_strings)
    return full_stats, None

def get_league_leaders(stat: str, season: str = None):
    stat = stat.lower()
    
    league_stats = {
        "points": "PTS",
        "assists": "AST",
        "rebounds": "REB",
        "blocks": "BLK",
        "steals": "STL",
        "turnovers": "TOV",
        "fg%": "FG_PCT",
        "fgm": "FGM",
        "3pm": "FG3M",
        "ftm": "FTM",
        "3p%": "FG3_PCT",
        "ft%": "FT_PCT",
        "minutes": "MIN"
    }

    per_game_stats = {
        "points": "PTS/G",
        "assists": "AST/G",
        "rebounds": "REB/G",
        "blocks": "BLK/G",
        "steals": "STL/G",
        "turnovers": "TOV/G",
        "fgm": "FGM / G",
        "3pm": "FG3M/G",
        "ftm": "FTM / G",
        "minutes": "MIN/G",
    }

    pct_stats = {
        "fg%": "FG_PCT",
        "3p%": "FG3_PCT",
        "ft%": "FT_PCT",
    }

    stat_display_names = {
        "points": "PTS",
        "assists": "AST",
        "rebounds": "REB",
        "blocks": "BLK",
        "steals": "STL",
        "turnovers": "TOV",
        "fg%": "FG%",
        "fgm": "FGM",
        "3pm": "3PM",
        "ftm": "FTM",
        "3p%": "3P%",
        "ft%": "FT%",
        "minutes": "MIN"
    }

    # Validate stat
    valid_stats = set(league_stats) | set(per_game_stats) | set(pct_stats)
    if stat not in valid_stats:
        return None, f"Invalid stat, use !stathelp to view valid stats."

    # Convert season to season_id
    season_id = None
    if season:
        season_id = season_to_year(season)
        if not season_id:
            return None, f"Invalid season format. Please use a 4 digit year like 2025."

    try:
        leaders = leagueleaders.LeagueLeaders(
            season=season_id if season_id else "", 
            season_type_all_star="Regular Season"
        )
        df = leaders.get_data_frames()[0]
        print(df.columns)
    except Exception as e:
        return None, "Error getting stats"
    
    if stat == "fg%":
        df=df[df["FGM"] > 150]
    elif stat == "3p%":
        df=df[df["FG3M"] > 82]
    elif stat == "ft%":
        df=df[df["FTM"] > 150]

    # Process DataFrame
    if stat in league_stats:
        base_column = league_stats[stat]
        df = df[df["GP"] > 0]
        
        if stat in per_game_stats:
            per_game_column = per_game_stats[stat]
            df.loc[:, per_game_column] = df[base_column] / df["GP"]
            sort_column = per_game_column
        else:
            sort_column = base_column

        df = df.sort_values(by=sort_column, ascending=False).head(10)

    else:
        # Percentage stats
        sort_column = pct_stats[stat]
        df = df.sort_values(by=sort_column, ascending=False).head(10)

    # Format results
    results = []
    for rank, (_, row) in enumerate(df.iterrows(), start=1):
        player = row['PLAYER']
        value = row[sort_column]
        displayed_stat = stat_display_names.get(stat, stat.upper())
        if stat in pct_stats and isinstance(value, (int, float)):
            value *= 100
        formatted_value = f"{value:.1f}" if isinstance(value, (int, float)) else str(value)
        results.append(f"{rank}. {player} - {displayed_stat}: {formatted_value}")

    return "\n".join(results), None


async def charlimit(ctx, message: str):
    if not message:
        await ctx.send("No data to display.")
        return

    if len(message) > 1900:
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        for chunk in chunks:
            await ctx.send(f"```{chunk}```")
    else:
        await ctx.send(f"```{message}```")


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
        f"Hello {ctx.author}, this is the 12th code update!"
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
        "!leaders        - Show the league's top 10 leaders in a stat. Format: !leaders Assists 2025\n"
        "!alltime        - Show the all-time leaders for a stat. Format: !alltime Points"
        "!randomplayer   - Generates a random NBA player. Format: !randomplayer 2016"
        "```"
        "\n**Note:** If no year is added, the default will be all time."
    )
    await ctx.send(help_text)
# !commands
@bot.command(name = 'stathelp')
async def commands(ctx):
    stathelp_text = (
        "```"
        "Here's a list of valid stats:\n\n"
        "Points     - View the league leaders in Points per Game"
        "Assists    - View the league leaders in Assists per Game"
        "Rebounds   - View the league leaders in Rebounds per Game"
        "Blocks     - View the league leaders in Blocks per Game"
        "Steals     - View the league leaders in Steals per Game"
        "Turnovers  - View the league leaders in Turnovers per Game"
        "FG%        - View the league leaders in Shooting Efficiency"
        "3PM        - View the league leaders in 3 Pointers Made per Game"
        "3P%        - View the league leaders in 3 Point Percentage"
        "FT%        - View the league leaders in Free Throw Percentage"
        "Minutes    - View the league leaders in Minutes per Game"
        "```"
    )
    await ctx.send(stathelp_text)

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

    await charlimit(ctx, stats)

# !teamstats
@bot.command(name = 'teamstats')
async def teamstats(ctx, *, args: str):
    parts = args.rsplit(maxsplit=1)
    if re.match(r"\d{4}", parts[-1]):
        team_name = parts[0]
        season = parts[-1]
    else:
        team_name = args 
        season = None

    if season:
        await ctx.send(f"Getting stats for {team_name} in {season}")
    else:
        await ctx.send(f"Please input a season. Format: !teamstats {team_name} 2025")

    stats, error = get_team_stats(team_name, season)

    await charlimit(ctx, stats)

# !teamroster

# !compare

# !leaders
@bot.command(name = 'leaders')
async def leagueleadercmd(ctx, *, args: str):
    parts = args.rsplit(maxsplit=1)
    if re.match(r"\d{4}", parts[-1]):
        stat = parts[0]
        season = parts[-1]
    else:
        stat = args 
        season = None

    if season:
        await ctx.send(f"Getting stats for {stat} in {season}")
    else:
        await ctx.send(f"For all time stats, use !alltimeleaders")

    stats, error = get_league_leaders(stat, season)

    await charlimit(ctx, stats)

# !alltime
        
# !shotchart

# Run the bot with your Discord bot token
print
if token:
    bot.run(token)
else: 
    print("Could not find token")
