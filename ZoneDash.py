import dash
from dash import dcc, html,dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pybaseball.cache
import requests
import json
import pandas as pd
import pybaseball
session = requests.Session()

pybaseball.cache.enable()
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    html.Div([
        dcc.Input(id='gamepk-input', type='text', placeholder='Enter Game PK', style={'marginRight': '10px'}),
        dcc.Input(id='pitcher-name-input', type='text', placeholder='Enter Pitcher Name', style={'marginRight': '10px'}), html.Button('Fetch Data', id='fetch-button', n_clicks=0),
                html.Div([
        dcc.Dropdown(
            id='pitcher-dropdown',
            options=[],  # This will be populated dynamically
            placeholder='Select a pitcher',
            style={'width': '300px', 'margin': '10px'}
        )
    ], style={'text-align': 'center'}),
       
        dcc.Interval(id='interval-component', interval=20*10000000, n_intervals=0)
    ], style={'text-align': 'center', 'padding': '10px'}),
    html.Div([
        html.Div([
            dcc.Graph(id='strike-zone-graph', style={'height': '40vh', 'width': '80%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '33.33%', 'padding': '0', 'margin': '0'}),
        html.Div([
            dcc.Graph(id='current-zone-graph', style={'height': '40vh', 'width': '80%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '33.33%', 'padding': '0', 'margin': '0'}),
    html.Div([
            dcc.Graph(id='win-probability-graph', style={'height': '40vh', 'width': '100%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '33.33%', 'padding': '0', 'margin': '0'})
    ], style={'width': '100%', 'padding': '0', 'margin': '0'}),
    
    html.Div([
    html.Div(id='pitcher-table-container', style={'width': '50%'}),
    html.Div(id='batter-table-container', style={'width': '50%'})
], style={'display': 'flex'}),html.Div([
        dcc.Graph(id='live-pitch-data-graph', style={'height': '50vh', 'width': '100%', 'margin': '0'})
    ]),
    html.Div([
        dcc.Checklist(
            id='toggle-labels',
            options=[
                {'label': 'Show Labels', 'value': 'show'}
            ],
            value=[],
            style={'display': 'inline-block'}
        )
    ])
    
])
color_dict = {
                    'Changeup': 'red',
                    'Curveball': 'blue',
                    'Cutter': 'green',
                    'Eephus': 'yellow',
                    'Forkball': 'purple',
                    'Four-Seam Fastball': 'orange',
                    '4-Seam Fastball': 'orange',
                    'Knuckleball': 'pink',
                    'Knuckle Curve': 'cyan',
                    'Screwball': 'magenta',
                    'Sinker': 'brown',
                    'Slider': 'lime',
                    'Slurve': 'teal',
                    'Splitter': 'navy',
                    'Sweeper': 'maroon'
                }
batting_stats = pybaseball.batting_stats(2024,qual=0)
pitching_stats = pybaseball.pitching_stats(2024,qual=0)


@app.callback(
    Output('pitcher-name-input', 'value'),
    Input('pitcher-dropdown', 'value')
)
def update_pitcher_name_input(selected_pitcher):
    return selected_pitcher or ''

@app.callback(
    Output('pitcher-dropdown', 'options'),
    Input('fetch-button', 'n_clicks'),
    State('gamepk-input', 'value')
)
def update_pitcher_dropdown(n_clicks, gamepk):
    if n_clicks > 0:
        # Fetch the game data using the gamepk
        game_data = fetch_game_data(gamepk)  # Replace with your function to fetch game data

        # Extract the pitcher names from the game data
        pitcher_names = extract_pitcher_names(game_data)  # Replace with your function to extract pitcher names

        # Create the options for the dropdown
        options = [{'label': name, 'value': name} for name in pitcher_names]

        return options

    # If the 'Fetch Data' button has not been clicked, return an empty list
    return []

@app.callback(
    Output('pitcher-table-container', 'children'),
    Output('batter-table-container', 'children'),
    [Input('fetch-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State('gamepk-input', 'value'), State('pitcher-name-input', 'value')]  # Add the text box's id and value property
)
def update_stat_table(n_clicks, n_intervals, gamepk, pitcher_name):  # Add a parameter for the text box's value
    if n_clicks > 0 and gamepk:
        game_data = fetch_game_data(gamepk)
        current_play_data = fetch_current_play_data(game_data)


        # Extract batter's and pitcher's full name
        batter_name = current_play_data.get('matchup', {}).get('batter', {}).get('fullName', 'Unknown')

        batter_player_dict = fetch_batter_statline(batter_name)
        pitcher_player_dict = fetch_pitcher_statline(pitcher_name)

        if isinstance(batter_player_dict, str) or isinstance(pitcher_player_dict, str):  # If no stats were found
            return [],[]

        # Create the columns for each table
        batter_columns = [{"name": i, "id": i} for i in batter_player_dict.keys()]
        pitcher_columns = [{"name": i, "id": i} for i in pitcher_player_dict.keys()]

        # Create the data for each table
        batter_data = [batter_player_dict]
        pitcher_data = [pitcher_player_dict]

        # Create the tables
        batter_table = dash_table.DataTable(
            id='batter-slashline-table',
            columns=batter_columns,
            data=batter_data,
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': 'paleturquoise',
                'fontWeight': 'bold'
            },
            style_data={
                'backgroundColor': 'lavender',
            }
        )

        pitcher_table = dash_table.DataTable(
            id='pitcher-slashline-table',
            columns=pitcher_columns,
            data=pitcher_data,
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': 'paleturquoise',
                'fontWeight': 'bold'
            },
            style_data={
                'backgroundColor': 'lavender',
                'minWidth': '25px',  # set minimum cell width
                'width': '25px'
            },
            style_table={'height': '10vh', 'width': '95%', 'overflowY': 'auto', 'margin': 'auto'}
        )

        return [pitcher_table], [batter_table]

    return [], []


@app.callback(
    Output('current-zone-graph', 'figure'),
    [Input('fetch-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State('gamepk-input', 'value'), State('pitcher-name-input', 'value')]
)
def update_current_zone(n_clicks, n_intervals, game_pk, pitcher_name):
    if n_clicks > 0 and game_pk:
        game_data = fetch_game_data(game_pk)
        if game_data and pitcher_name:
            strike_zone_data = fetch_strike_zone_data(game_data)
            current_play_data = fetch_current_play_data(game_data)

            # Extract batter's full name
            batter_name = current_play_data.get('matchup', {}).get('batter', {}).get('fullName', 'Unknown')
            pitcher_name = current_play_data.get('matchup', {}).get('pitcher', {}).get('fullName', 'Unknown')

            # Check if playEvents is a list
            if isinstance(current_play_data.get('playEvents'), list):
                fig = go.Figure()

                # Draw the strike zone
                fig.add_shape(type="rect",
                              x0=-0.7083, y0=strike_zone_data['bottom'],
                              x1=0.7083, y1=strike_zone_data['top'],
                              line=dict(color="RoyalBlue"))

                # Loop over all play events
                for play_event in current_play_data['playEvents']:
                    pitch_data = play_event.get('pitchData', {})
                    coordinates = pitch_data.get('coordinates', {})
                    pitch_type = play_event.get('details', {}).get('type', {}).get('description', 'Unknown')
                    pitch_speed = play_event.get('pitchData', {}).get('startSpeed', 'Unknown')
                    spin_rate = pitch_data.get('breaks', {}).get('spinRate', 'Unknown')
                    count = play_event.get('count', {}).get('balls', 0), play_event.get('count', {}).get('strikes', 0)
                    call = play_event.get('details', {}).get('call', {}).get('description', 'Unknown')
                    inning = play_event.get('about', {}).get('inning', 'Unknown')
                    

                    px = coordinates.get('pX')
                    pz = coordinates.get('pZ')

                    
                    color = color_dict.get(pitch_type, 'black')  # Use black for unknown pitch types

                    fig.add_trace(go.Scatter(
        x=[px],
        y=[pz],
        mode='markers',
        marker=dict(color=color, size=15),
        name=pitch_type,
        hovertemplate=f"type: {pitch_type},<br>speed: {pitch_speed} mph,<br>spin rate: {spin_rate},<br>count: {count},<br>call: {call},<br>batter: {batter_name},<br>inning: {inning}"
    ))

                # Set figure properties
                fig.update_layout(
                    title=f"Strike Zone with Current Pitch Location for {pitcher_name}",  # Update the title with the batter's name
                    xaxis_title="Width (feet)",
                    yaxis_title="Height (feet)",
                    showlegend=False,
                    xaxis=dict(scaleanchor="y", scaleratio=1),
                    yaxis=dict(
                        range=[0, 5]
                    ),
                    xaxis_range=[-2.5, 2.5]
                )
                return fig
    return go.Figure()  # Return an empty figure if no data
    


def fetch_pitcher_statline(pitcher_name):
    # Define the stats we care about
    stats_we_care_about = ['Name','Age','AVG','G','BABIP','BB','HR','ER','ERA','FIP','WHIP','HBP','IP','SO','SV','WAR','xFIP']

    # Filter the stats for the specific batter
    player_stats = pitching_stats.query('Name == @pitcher_name')

    # Check if the DataFrame is empty
    if player_stats.empty:
        return f"No stats found for {pitcher_name}"

    # Get the stats we care about and store them in a dictionary
    player_dict = player_stats[stats_we_care_about].iloc[0].to_dict()

    return player_dict

def fetch_batter_statline(batter_name):
    # Define the stats we care about
    stats_we_care_about = ['Name','Age','G', 'AVG','BABIP','BB', 'HR','PA', 'H',   'RBI',   'OBP', 'OPS', 'ISO', 'K%',  'wOBA',  'wRC+','WAR']

    # Filter the stats for the specific batter
    player_stats = batting_stats.query('Name == @batter_name')

    # Check if the DataFrame is empty
    if player_stats.empty:
        return f"No stats found for {batter_name}"

    # Get the stats we care about and store them in a dictionary
    player_dict = player_stats[stats_we_care_about].iloc[0].to_dict()

    return player_dict


@app.callback(
    Output('win-probability-graph', 'figure'),
    [Input('fetch-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State('gamepk-input', 'value')]
)
def update_win_probability_graph(n_clicks, n_intervals, game_pk):
    if n_clicks > 0 and game_pk:
        game_data = fetch_game_data(game_pk)
        previous_result = extract_current_result(game_data)
        if game_data:
            home_win_probs, away_win_probs, home_team, away_team = extract_win_probabilities(game_data)

            if home_win_probs is not None and away_win_probs is not None:
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=list(range(len(home_win_probs))),
                    y=home_win_probs,
                    mode='lines',
                    name=home_team,
                    line=dict(color='blue')
                ))

                fig.add_trace(go.Scatter(
                    x=list(range(len(away_win_probs))),
                    y=away_win_probs,
                    mode='lines',
                    name=away_team,
                    line=dict(color='red')
                ))

                # Check if previous_result is None
                if previous_result is None:
                    previous_result = 'No current at bat'

                fig.update_layout(
                    title=home_team+" vs "+away_team+ " Win Probability<br>Previous Result: "+previous_result,
                    yaxis_title="Win Probability",
                    xaxis_title="Time",
                    showlegend=True
                )

                return fig

    return go.Figure()  # Return an empty figure if no data

@app.callback(
    Output('live-pitch-data-graph', 'figure'),
    [Input('fetch-button', 'n_clicks'),
     Input('interval-component', 'n_intervals'),
     Input('toggle-labels', 'value')],  # This takes the state of the checkbox
    [State('gamepk-input', 'value'),
     State('pitcher-name-input', 'value')]
)
def update_graph_live(button_clicks, n_intervals, toggle_labels, game_id, pitcher_name):
    if not game_id or not pitcher_name:
        return go.Figure()

    pitch_data = PitchData(game_id, pitcher_name)
    filtered_data = pitch_data.get_filtered_data()

    fig = go.Figure()
    if not filtered_data.empty:
        mode = 'markers+lines+text' if toggle_labels else 'markers+lines'  # Decide whether to include text based on toggle_labels
        fig.add_trace(go.Scatter(
            x=list(range(len(filtered_data))), 
            y=filtered_data['start_speed'],
            mode=mode,  # Use the mode variable here
            name='Pitch Speed',
            text=filtered_data.apply(lambda x: f"{x['pitch_name']}: {x['start_speed']} mph", axis=1),
            textposition='top center',
            hoverinfo='text',
            hovertemplate='%{text}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=list(range(len(filtered_data))), 
            y=filtered_data['spin_rate'],
            mode=mode,  # Use the mode variable here
            name='Spin Rate',
            yaxis='y2', 
            text=filtered_data.apply(lambda x: f"{x['pitch_name']}: {x['spin_rate']} rpm", axis=1),
            textposition='top center',
            hoverinfo='text',
            hovertemplate='%{text}<extra></extra>'
        ))
        
        fig.update_layout(
            yaxis=dict(title='Start Speed (mph)'),
            yaxis2=dict(title='Spin Rate (rpm)', overlaying='y', side='right')
        )
        fig.update_layout(transition={'duration': 500})

    return fig

@app.callback(
    Output('live-update-graph', 'figure'),
    [Input('submit-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State('input-gamepk', 'value'), State('input-pitcher-name', 'value')],
)
def update_graph_live(button_clicks, n_intervals, game_id, pitcher_name):
    # Fetch and filter data regardless of which input triggered the update
    if not game_id or not pitcher_name:
        return go.Figure()

    pitch_data = PitchData(game_id, pitcher_name)
    filtered_data = pitch_data.get_filtered_data()

    fig = go.Figure()
    if not filtered_data.empty:
        text_labels = filtered_data.apply(lambda x: f"Pitch Type: {x['pitch_name']}<br>" +
                                                    f"Result: {x['result']}<br>" +
                                                    f"Description: {x['description']}<br>" +
                                                    f"Call: {x['call']}<br>" +
                                                    f"Batter: {x['batter_name']}<br>" +
                                                    f"Speed: {x['start_speed']} mph<br>" +
                                                    f"Spin Rate: {x['spin_rate']} rpm", axis=1)
        fig.add_trace(go.Scatter(
            x=list(range(len(filtered_data))), y=filtered_data['start_speed'],
            mode='markers+lines', name='Pitch Speed',
            text=text_labels, hoverinfo='text+y'
        ))
        fig.add_trace(go.Scatter(
            x=list(range(len(filtered_data))), y=filtered_data['spin_rate'],
            mode='markers+lines', name='Spin Rate',
            yaxis='y2', text=text_labels, hoverinfo='text+y'
        ))

        fig.update_layout(
            yaxis=dict(title='Start Speed (mph)'),
            yaxis2=dict(title='Spin Rate (rpm)', overlaying='y', side='right')
        )
        fig.update_layout(transition={'duration': 500})

    return fig

@app.callback(
    Output('strike-zone-graph', 'figure'),
    [Input('fetch-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State('gamepk-input', 'value'), State('pitcher-name-input', 'value')]
)
def update_strike_zone(n_clicks, n_intervals, game_pk, pitcher_name):
    if n_clicks > 0 and game_pk:
        game_data = fetch_game_data(game_pk)
        if game_data and pitcher_name:
            strike_zone_data = fetch_strike_zone_data(game_data)
            pitch_locations = get_pitcher_data(game_data, pitcher_name)
            
            fig = go.Figure()

            # Draw the strike zone
            fig.add_shape(type="rect",
                          x0=-0.7083, y0=strike_zone_data['bottom'],
                          x1=0.7083, y1=strike_zone_data['top'],
                          line=dict(color="RoyalBlue"))

            # Plot each pitch location
            for location in pitch_locations:
                fig.add_trace(go.Scatter(
                    x=[location['px']],
                    y=[location['pz']],
                    mode='markers+text',
                    marker=dict(color=color_dict.get(location['pitch_name'], '#000'), size=15),  # Use the color from the dictionary
                    name='Pitch Location',
                    hovertemplate=f"px: {location['px']}, pz: {location['pz']},<br>start_speed: {location['start_speed']},<br>result: {location['result']},<br>spin_rate: {location['spin_rate']},<br>call: {location['call']},<br>batter: {location['batter_name']},<br>inning: {location['inning']},<br>pitch_name: {location['pitch_name']}"
                ))

            # Set figure properties
            fig.update_layout(
                title="Strike Zone with All Pitch Locations",
                xaxis_title="Width (feet)",
                yaxis_title="Height (feet)",
                showlegend=False,
                xaxis=dict(scaleanchor="y", scaleratio=1),
                yaxis=dict(range=[0, 5]),
                xaxis_range=[-2.5, 2.5]
            )
            return fig
    return go.Figure()  # Return an empty figure if no data

def extract_pitcher_names(game_data):
    """Extracts the names of the pitchers who have pitched in the game."""
    pitcher_names = []

    # Loop through the home and away pitchers
    for team in ['home_pitchers', 'away_pitchers']:
        for playerid, pitches in game_data.get(team, {}).items():
            # Extract the pitcher name from the first dictionary in the list
            pitcher_name = pitches[0].get('pitcher_name')
            if pitcher_name:
                pitcher_names.append(pitcher_name)

    return pitcher_names

def get_pitcher_data(game_data, pitcher_name=None):
    """Extracts all or specific pitcher's pitch data."""
    pitch_data = []
    for key in ['home_pitchers', 'away_pitchers']:
        pitchers = game_data.get(key, {})
        for pitcher_id, pitches in pitchers.items():
            if pitcher_name is None or pitches[0]['pitcher_name'].lower().strip() == pitcher_name.lower().strip():
                pitch_data.extend(extract_pitch_details(pitches))
    return pitch_data

def extract_pitch_details(pitches):
    """Extracts details of pitches."""
    #print(f"Input pitches: {pitches}")  # Print the input
    pitches = pitches if isinstance(pitches, list) else [pitches]
    pitch_details_list = []
    for pitch in pitches:
        if 'px' in pitch and 'pz' in pitch:
            pitch_details = {
                'px': pitch['px'], 'pz': pitch['pz'],
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
                'inning': pitch.get('inning'),
                'pitcher_name': pitch.get('pitcher_name')
            }
            pitch_details_list.append(pitch_details)
        else:
            print(f"Pitch without 'px' or 'pz': {pitch}")  # Print the pitch that doesn't contain 'px' or 'pz'
    return pitch_details_list

def extract_win_probabilities(game_data):
    """Extracts win probabilities and team names."""
    try:
        wpa_list = game_data['scoreboard']['stats']['wpa']['gameWpa']
        home_win_probs = [wpa['homeTeamWinProbability'] for wpa in wpa_list]
        away_win_probs = [wpa['awayTeamWinProbability'] for wpa in wpa_list]
        home_team = game_data['home_team_data']['name']
        away_team = game_data['away_team_data']['name']
        return home_win_probs, away_win_probs, home_team, away_team
    except KeyError:
        return None, None, None, None
def extract_current_result(game_data):
    """Extracts the result of the current play."""
    try:
        play_events = game_data['scoreboard']['currentPlay']['playEvents']
        if play_events:
            return play_events[-1]['details']['description']
    except KeyError:
        return 'No current play ongoing.'

def extract_pitching_events(game_data):
    """Extracts pitching events from the game data."""
    pitching_events = []
    try:
        pitch_velocity_data = game_data.get('away_pitchers', {}) | game_data.get('home_pitchers', {})
        for pitcher_data in pitch_velocity_data.values():
            pitching_events.extend(extract_pitch_details(pitcher_data))
    except KeyError as e:
        print(f"KeyError: {e}")
    return pitching_events

def extract_current_at_bat_pitch_locations(game_data):
    """Extracts pitch locations for the current at bat."""
    locations = []
    try:
        current_play = game_data['scoreboard']['currentPlay']['playEvents']
        for pitch in current_play:
            if 'pitchData' in pitch and 'coordinates' in pitch['pitchData']:
                coord = pitch['pitchData']['coordinates']
                if 'pX' in coord and 'pZ' in coord:
                    locations.append({
                        'px': coord['pX'], 'pz': coord['pZ'],
                        'pitch_type': pitch['pitchData'].get('pitch_type'),
                        'start_speed': pitch['pitchData'].get('start_speed'),
                        'end_speed': pitch['pitchData'].get('end_speed'),
                        'spin_rate': pitch['pitchData'].get('spin_rate'),
                        'result': pitch['pitchData'].get('result'),
                        'description': pitch['pitchData'].get('des'),
                        'call': pitch['pitchData'].get('call_name'),
                        'batter_name': pitch['pitchData'].get('batter_name'),
                        'ab_number': pitch['pitchData'].get('ab_number'),
                        'pitch_name': pitch['pitchData'].get('pitch_name'),
                        'pitch_types': pitch['pitchData'].get('pitch_types')
                    })
    except KeyError:
        print("No current at bat or incomplete data.")
    return locations




 




def fetch_game_data(game_pk):
    """Fetches game data from Baseball Savant and exports pitcher data to JSON."""
    url = f"https://baseballsavant.mlb.com/gf?game_pk={game_pk}"
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


def fetch_all_pitch_locations(game_data):
    """Fetches all px and pz values for pitches from home and away pitchers."""
    locations = []
    try:
        # Combine both home and away pitchers into one dictionary
        all_pitchers = {**game_data.get('home_pitchers', {}), **game_data.get('away_pitchers', {})}

        # Iterate through each pitcher's pitches to collect px and pz
        for pitcher_id, pitches in all_pitchers.items():
            for pitch in pitches:
                if 'px' in pitch and 'pz' in pitch:
                    locations.append({'px': pitch['px'], 'pz': pitch['pz']})
    except KeyError as e:
        print(f"KeyError extracting pitching events: {e}")

    return locations



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
        else:
            print("Strike zone data not found in the first play event.")
    else:
        print("No play events found for the current play.")

    
    # Return default values if the necessary data is not found or the request fails
    return {'top': 3.5, 'bottom': 1.5}







def fetch_current_play_data(game_data):
    """Extracts current play details from game data."""
    # Navigate to the correct path to extract current play data
    current_play = game_data.get('scoreboard', {}).get('currentPlay', {})
    if current_play:
        return current_play
    else:
        print("No current play data found.")
        return {}

class PitchData:
    def __init__(self, game_id, pitcher_name):
        self.game_id = game_id
        self.pitcher_name = pitcher_name

    def fetch_game_data_from_savant(self):
        url = f"https://baseballsavant.mlb.com/gf?game_pk={self.game_id}"
        response = session.get(url)
        return response.json() if response.status_code == 200 else None

    def get_filtered_data(self):
        game_data = self.fetch_game_data_from_savant()
        if game_data:
            pitching_events = extract_pitching_events(game_data)
            return self.filter_pitch_data(pitching_events)
        else:
            print(f"Error fetching data for game {self.game_id}")
            return pd.DataFrame()

 

    def filter_pitch_data(self, pitch_data):
        pitch_data_df = pd.DataFrame(pitch_data)
        return pitch_data_df[(pitch_data_df['pitcher_name'] == self.pitcher_name)]



if __name__ == '__main__':
    app.run_server(debug=True)
