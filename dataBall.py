import pybaseball
from unidecode import unidecode


player_batting_stats = pybaseball.batting_stats(2024,qual=1)
qualified_player_batting_stats = pybaseball.batting_stats(2024)
player_pitching_stats = pybaseball.pitching_stats(2024,qual=1)
qualified_player_pitching_stats = pybaseball.pitching_stats(2024)
team_batting_stats = pybaseball.team_batting(2024)
team_pitching_stats = pybaseball.team_pitching(2024)

def extract_team_player_stats(team_name):
    
    # Define the stats we care about
    stats_we_care_about = ['AVG', 'BABIP', 'BB', 'Balls', 'HR', 'OBP', 'OPS', 'PA', 'R', 'RBI', 'SLG', 'SO', 'WAR', 'wOBA', 'wRC+', 'ISO', 'K%', 'BB%']
    
    stats = player_batting_stats
    # Filter players by the specified team
    team_players = player_batting_stats[player_batting_stats['Team'] == team_name]
    
    # Create a dictionary to hold each player's stats
    player_stats_dict = {}
    
    for index, row in team_players.iterrows():
        player_name = row['Name']
        player_stats = row[stats_we_care_about].to_dict()
        
        # Round and format each stat
        for key, value in player_stats.items():
            if isinstance(value, float):
                if key.endswith('%'):
                    player_stats[key] = f"{round(value * 100, 2)}%"
                else:
                    player_stats[key] = round(value, 3)
        
        # Store in dictionary
        player_stats_dict[player_name] = player_stats

    return player_stats_dict

#Takes the dataframe, stat we want to filter by, and the team name if we want to filter by team
def extract_stats(df, stats_we_care_about, team_name=None):
    averages = calculate_averages(df, stats_we_care_about, team_name)
    formatted_stats = format_stats(averages)
    return formatted_stats

# Extracts the pitching stats for a specific team
def extract_league_pitching_team_stats(team_name=None):
    stats_we_care_about = ['AVG','BABIP','Balls','Strikes','BB','ER','ERA','FIP','WHIP','H','HR','WAR','xFIP']
    return extract_stats(team_pitching_stats, stats_we_care_about, team_name)

# Extracts the batting stats for a specific team
def extract_league_batting_team_stats(team_name=None):
    stats_we_care_about = ['AVG', 'BABIP','BB','Balls','HR','OBP','OPS','PA','R','RBI','SLG','SO','WAR','wOBA']
    return extract_stats(team_batting_stats, stats_we_care_about, team_name)

#Extracts the pitching stats for a specific player
def extract_pitch_statline(pitcher_name):
    stats_we_care_about = ['K/9','H/9', 'BB%','BABIP', 'ERA', 'FIP', 'WHIP', 'SIERA', 'xFIP']
    return extract_statline(pitcher_name, player_pitching_stats, team_pitching_stats, stats_we_care_about)

#Extracts the batting stats for a specific player
def extract_batter_statline(batter_name):
    stats_we_care_about = ['AVG', 'SLG', 'OBP', 'OPS', 'BABIP', 'ISO','BB%', 'K%', 'wOBA', 'wRC+']
    return extract_statline(batter_name, player_batting_stats, team_batting_stats, stats_we_care_about)


#Extracts the pitchers names for the drop down menu to select a pitcher
def extract_pitcher_names(game_data):
    pitcher_names = []
    # Loop through the home and away pitchers
    for team in ['home_pitchers', 'away_pitchers']:
        for playerid, pitches in game_data.get(team, {}).items():
            # Extract the pitcher name from the first dictionary in the list
            pitcher_name = pitches[0].get('pitcher_name')
            if pitcher_name:
                pitcher_names.append(pitcher_name)

    return pitcher_names

#Extracts all or specific pitcher's pitch data. If no pitcher is specified, all pitchers' data is returned
def get_pitcher_data(game_data, pitcher_name=None):
    pitch_data = []
    for key in ['home_pitchers', 'away_pitchers']:
        pitchers = game_data.get(key, {})
        for pitcher_id, pitches in pitchers.items():
            if pitcher_name is None or pitches[0]['pitcher_name'].lower().strip() == pitcher_name.lower().strip():
                pitch_data.extend(extract_pitch_details(pitches))
    return pitch_data

#Calculates the averages for the stats we care about
def calculate_averages(df, stats_we_care_about, team_name=None):
    if team_name:
        df = df[df['Team'] == team_name]
    averages = df[stats_we_care_about].mean().to_dict()
    return averages

#Properly formats % based stats as well as rounds all other stats to 3 decimal places
def format_stats(stats):
    for key, value in stats.items():
        if isinstance(value, float):
            if key.endswith('%'):
                stats[key] = f"{round(value * 100, 2)}%"
            else:
                stats[key] = round(value, 3)
    return stats






#Chooses which stats to extract from the pitch data
def extract_pitch_data(pitch):
    return {
        'px': pitch.get('px'), 'pz': pitch.get('pz'),
        'pitch_type': pitch.get('pitch_type'),
        'start_speed': pitch.get('start_speed'),
        'end_speed': pitch.get('end_speed'),
        'spin_rate': pitch.get('spin_rate'),
        'result': pitch.get('result'),
        'description': pitch.get('des'),
        'call': pitch.get('call_name'),
        'batter_name': pitch.get('batter_name'),
        'ab_number': pitch.get('ab_number'),
        'pitch_name': pitch.get('pitch_name'),
        'pitch_types': pitch.get('pitch_types'),
        'inning': pitch.get('inning', None),  # Optional, might not be in all pitch data
        'pitcher_name': pitch.get('pitcher_name', None)  # Optional
    }

#Extracts the pitch details for the current play
def extract_current_pitch_details(game_data):
    locations = []
    try:
        current_play = game_data['scoreboard']['currentPlay']['playEvents']
        for pitch in current_play:
            if 'pitchData' in pitch and 'coordinates' in pitch['pitchData']:
                coord = pitch['pitchData']['coordinates']
                if 'pX' in coord and 'pZ' in coord:
                    pitch_info = {
                        'px': coord['pX'], 'pz': coord['pZ']
                    }
                    pitch_info.update(pitch['pitchData'])
                    locations.append(extract_pitch_data(pitch_info))
    except KeyError:
        print("No current at bat or incomplete data.")
    return locations

#Extracts the cumulative pitch details for the current game
def extract_pitch_details(pitches):
    pitches = pitches if isinstance(pitches, list) else [pitches]
    pitch_details_list = []
    for pitch in pitches:
        if 'px' in pitch and 'pz' in pitch:
            pitch_details_list.append(extract_pitch_data(pitch))
        else:
            print(f"Pitch without 'px' or 'pz': {pitch}")
    return pitch_details_list



#Extracts the WPA(Win Probability Added) that is used to calculate the win probability of the home and away teams throughout the game and the team names
def extract_win_probabilities(game_data):
    try:
        wpa_list = game_data['scoreboard']['stats']['wpa']['gameWpa']
        home_win_probs = [wpa['homeTeamWinProbability'] for wpa in wpa_list]
        away_win_probs = [wpa['awayTeamWinProbability'] for wpa in wpa_list]
        home_team = game_data['home_team_data']['abbreviation']
        away_team = game_data['away_team_data']['abbreviation']

        return home_win_probs, away_win_probs, home_team, away_team
    except KeyError:
        return None, None, None, None
    

#Extracts the result of the current play
def extract_current_result(game_data):
    try:
        play_events = game_data['scoreboard']['currentPlay']['playEvents']
        if play_events:
            return play_events[-1]['details']['description']
    except KeyError:
        return 'No current play ongoing.'
    

#Extracts pitching events from the game data
def extract_pitching_events(game_data):
    pitching_events = []
    try:
        pitch_velocity_data = game_data.get('away_pitchers', {}) | game_data.get('home_pitchers', {})
        for pitcher_data in pitch_velocity_data.values():
            pitching_events.extend(extract_pitch_details(pitcher_data))
    except KeyError as e:
        print(f"KeyError: {e}")
    return pitching_events





def extract_statline(player_name, player_stats_df, team_stats_df, stats_we_care_about):
    # Clean up the player's name: strip spaces, convert to lower case, remove accents
    player_name_cleaned = unidecode(player_name.strip().lower())

    # Filter the stats for the specific player, converting the Name column to lower case for the comparison
    player_stats = player_stats_df[player_stats_df['Name'].apply(lambda x: unidecode(x.lower().strip())) == player_name_cleaned]

    # Check if the DataFrame is empty
    if player_stats.empty:
        print(f"No stats found for {player_name}")
        return {}, {}, {}

    # Get the stats we care about and store them in a dictionary
    player_dict = player_stats[stats_we_care_about].iloc[0].to_dict()
    team = player_stats['Team'].iloc[0]

    # Insert the player's name at the beginning of the dictionary
    player_dict = {'Name': player_name, **player_dict}

    # Calculate the league average for the stats we care about from team_stats_df
    league_average_dict = team_stats_df[stats_we_care_about].mean().to_dict()

    # Get the team average stats from the team_stats_df dataframe
    team_average_dict = team_stats_df[team_stats_df['Team'] == team].iloc[0].to_dict()

    # Insert "League Average" and "Team Average" at the beginning of the league and team average dictionaries
    league_average_dict = {'Name': 'League Average', **league_average_dict}
    team_average_dict = {'Name': team+' Average', **team_average_dict}

    # Use the round_stats function to round the stats in each dictionary
    player_dict = round_stats(player_dict)
    league_average_dict = round_stats(league_average_dict)
    team_average_dict = round_stats(team_average_dict)

    return player_dict, league_average_dict, team_average_dict


def extract_all_game_pitching_events(game_data):
    """Extracts all pitching events from a game and organizes them into a single list."""
    all_events = []

    # Loop through both home and away pitchers
    for team_key in ['home_pitchers', 'away_pitchers']:
        team_pitchers = game_data.get(team_key, {})
        
        for pitcher_id, plays in team_pitchers.items():
            for play_details in plays:
                # Format the count as 'Balls-Strikes'
                count = f"{play_details.get('balls', 0)}-{play_details.get('strikes', 0)}"
                
                # Get the current scores
                home_score = game_data.get('scoreboard', {}).get('linescore', {}).get('teams', {}).get('home', {}).get('runs', 0)
                away_score = game_data.get('scoreboard', {}).get('linescore', {}).get('teams', {}).get('away', {}).get('runs', 0)
                score = f"{home_score}-{away_score}"  # Display the score as 'home-away'
                
                event_info = {
                    'Pitch Type': play_details.get('pitch_type'),
                    'Batter': play_details.get('batter_name'),
                    'Pitcher': play_details.get('pitcher_name'),
                    'Outs': play_details.get('outs'),
                    'Count': count,
                    'Spin Rate': play_details.get('spin_rate'),
                    'Result': play_details.get('result'),
                    'Pitch Count': play_details.get('player_total_pitches'),
                    'Pitch #': play_details.get('game_total_pitches'),
                    'Score': score  # Add the current score
                }
                all_events.append(event_info)

    return all_events


#Rounds the stats in the dictionary to the appropriate number of decimal places/Percents
def round_stats(stats_dict):
    for key in stats_dict.keys():
        if isinstance(stats_dict[key], (int, float)):
            if key in ['Age', 'G', 'BB', 'HR', 'PA', 'H', 'RBI','SO','ER','HBP','IP']:
                stats_dict[key] = round(stats_dict[key])
            elif key.endswith('%'):
                stats_dict[key] = f"{round(stats_dict[key]*100, 2)}%"
            else:
                stats_dict[key] = round(stats_dict[key], 3)
    return stats_dict

