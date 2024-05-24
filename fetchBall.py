import json
import requests
from requests import session
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

