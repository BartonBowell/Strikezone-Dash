import json
import requests
from requests import session
import pandas as pd
import pybaseball
from pybaseball import get_splits,playerid_lookup



def fetch_current_play_data(game_data):
    """Extracts current play details from game data."""
    # Navigate to the correct path to extract current play data
    current_play = game_data.get('scoreboard', {}).get('currentPlay', {})
    if current_play:
        return current_play
    else:
        print("No current play data found.")
        return {}
    

def fetch_strike_zone_data(game_data):
    """Fetches game data from Baseball Savant and extracts strike zone details."""

    current_play = game_data.get('scoreboard', {}).get('currentPlay', {})
    play_events = current_play.get('playEvents', [])
    if play_events:
        pitch_data = play_events[0].get('pitchData', {})  # Access the first event's pitch data
        strike_zone_top = pitch_data.get('strikeZoneTop')
        strike_zone_bottom = pitch_data.get('strikeZoneBottom')
        
        if strike_zone_top is not None and strike_zone_bottom is not None:
            return {'top': strike_zone_top, 'bottom': strike_zone_bottom}
            
    # Return default values if the necessary data is not found or the request fails
    return {'top': 3.5, 'bottom': 1.5}


def fetch_combined_team_stats(year, end_year):
    team_batting_stats = pybaseball.team_batting(year, end_year)
    print(f"Number of columns in team_batting_stats: {len(team_batting_stats.columns)}")

    team_pitching_stats = pybaseball.team_pitching(year, end_year)
    print(f"Number of columns in team_pitching_stats: {len(team_pitching_stats.columns)}")

    # Find overlapping columns (excluding 'Team' and 'Season')
    overlapping_columns = set(team_batting_stats.columns) & set(team_pitching_stats.columns)
    overlapping_columns -= {'Team', 'Season'}

    # Rename overlapping columns in team_pitching_stats
    team_pitching_stats = team_pitching_stats.rename(columns={col: f'Pitching {col}' for col in overlapping_columns})

    # Merge the two tables on 'Team' and 'Season'
    combined_stats = pd.merge(team_batting_stats, team_pitching_stats, on=['Team', 'Season'])

    print(f"Number of columns in combined_stats: {len(combined_stats.columns)}")

    return combined_stats
def fetch_stats(start_year, end_year=None, data_type='batting', ind=1,qual='y'):
    """
    Fetches baseball statistics for the specified year range and data type,
    with an option to specify the ind parameter for individual or aggregated stats.

    Args:
        start_year (int): The starting year for fetching stats.
        end_year (int, optional): The ending year for fetching stats. Defaults to the same as start_year if None.
        data_type (str, optional): Type of stats to fetch, 'batting' or 'pitching'. Defaults to 'batting'.
        ind (int, optional): Indicator for individual (1) or aggregated (0) data. Defaults to 1.

    Returns:
        DataFrame: A DataFrame containing the fetched statistics.
    """
    if end_year is None:
        end_year = start_year

    if data_type == 'batting':
        player_batting_stats = pybaseball.batting_stats(start_year, end_year, ind=ind,qual=qual)
        return player_batting_stats
    elif data_type == 'pitching':
        player_pitching_stats = pybaseball.pitching_stats(start_year, end_year, ind=ind,qual=qual)
        return player_pitching_stats

def fetch_game_data(game_pk):
    """Fetches game data from Baseball Savant and exports pitcher data to JSON."""
    url = f"https://baseballsavant.mlb.com/gf?game_pk={game_pk}"
    session = requests.Session()  # Create a new session object
    response = session.get(url)
    if response.status_code == 200:
        try:
            game_data = response.json()
            # Export pitcher data to a JSON file for review
            pitcher_data = {
                'home_pitchers': game_data.get('home_pitchers', {}),
                'away_pitchers': game_data.get('away_pitchers', {})
            }
            with open('pitcher_data.json', 'w') as outfile:
                json.dump(pitcher_data, outfile, indent=4)
            return game_data
        except ValueError:
            print("Error parsing JSON")
            return None
    else:
        print("Failed to fetch data:", response.status_code)
        return None
    
def get_game_pks_and_teams():
    url = 'http://statsapi.mlb.com/api/v1/schedule/games/?sportId=1'
    response = requests.get(url)
    data = json.loads(response.text)

    game_info = []
    for date in data['dates']:
        for game in date['games']:
            game_pk = game['gamePk']
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            game_info.append((game_pk, away_team, home_team))
    
    return game_info



def get_bbref_id(first_name, last_name):
    """Fetches the bbref ID for a player using their first and last name."""
    try:
        player_ids = playerid_lookup(last_name, first_name)
        bbref_id = player_ids.loc[player_ids['key_bbref'].notna(), 'key_bbref'].values[0]
        return bbref_id
    except Exception as e:
        print(f"Failed to fetch bbref ID: {e}")
        return None

def fetch_splits(player_id, year=None, player_info=False, pitching_splits=False):
    """Fetches split stats for a player using the get_splits function from pybaseball."""
    try:
        if player_info:
            split_stats, player_info_dict = get_splits(player_id, year, player_info, pitching_splits)
            return split_stats, player_info_dict
        else:
            split_stats = get_splits(player_id, year, player_info, pitching_splits)
            return split_stats
    except Exception as e:
        print(f"Failed to fetch split stats: {e}")
        return None

def fetch_player_splits(full_name, year=None, player_info=False, pitching_splits=False):
    """Fetches split stats for a player using their full name."""
    first_name, last_name = full_name.split(' ')
    player_id = get_bbref_id(first_name, last_name)
    if player_id is not None:
        return fetch_splits(player_id, year, player_info, pitching_splits)
    else:
        print(f"Failed to fetch split stats for {full_name}")
        return None

