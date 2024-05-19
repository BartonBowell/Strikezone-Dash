import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import requests
import json
import seaborn as sns

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("MLB Strike Zone Visualization", style={'text-align': 'center'}),
    dcc.Graph(
        id='strike-zone-graph',
        style={'height': '100vh', 'width': '100vw'}  # This makes the graph full viewport height and width
    ),
    html.Div([
        dcc.Input(id='gamepk-input', type='text', placeholder='Enter Game PK', style={'marginRight': '10px'}),
        dcc.Input(id='pitcher-name-input', type='text', placeholder='Enter Pitcher Name', style={'marginRight': '10px'}),
        html.Button('Fetch Strike Zone', id='fetch-button', n_clicks=0)
    ], style={'text-align': 'center', 'padding': '10px'}),
    dcc.Interval(
        id='interval-component',
        interval=15*1000,  # in milliseconds
        n_intervals=0
    )
])

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
            #pitch_locations = extract_pitch_data_for_pitcher(game_data, pitcher_name)
            pitch_locations = extract_current_at_bat_pitch_locations(game_data)

            # Create a color map
            unique_pitch_types = set(location['pitch_type'] for location in pitch_locations)
            colors = sns.color_palette('hsv', len(unique_pitch_types)).as_hex()
            color_map = dict(zip(unique_pitch_types, colors))

            fig = go.Figure()

            # Draw the strike zone
            fig.add_shape(type="rect",
                          x0=-0.7083, y0=strike_zone_data['bottom'],
                          x1=0.7083, y1=strike_zone_data['top'],
                          line=dict(color="RoyalBlue"))

            # Plot each pitch location
            for location in pitch_locations:
                marker_style = {
                    'size': 25,
                    'color': color_map[location['pitch_type']],
                    'line': {'width': 2}
                }
                if location['call'] == 'In Play':
                    marker_style['symbol'] = 'circle-open-dot'
                    marker_style['line']['color'] = 'red'  # Outline color for "In Play" pitches
                    
                fig.add_trace(go.Scatter(
                    x=[location['px']],
                    y=[location['pz']],
                    mode='markers',
                    marker=marker_style,
                    name='Pitch Location',
                    hovertemplate=f"px: {location['px']}, pz: {location['pz']},<br>start_speed: {location['start_speed']},<br>result: {location['result']},<br>spin_rate: {location['spin_rate']},<br>call: {location['call']},<br>batter: {location['batter_name']},<br>pitch_name: {location['pitch_name']}"
                ))

            # Set figure properties
            fig.update_layout(
                title="Strike Zone with All Pitch Locations",
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

def fetch_game_data(game_pk):
    """Fetches game data from Baseball Savant and exports pitcher data to JSON."""
    url = f"https://baseballsavant.mlb.com/gf?game_pk={game_pk}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            game_data = response.json()  # Ensure this is JSON
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

def extract_all_pitch_locations(game_data):
    """Extracts all pitch locations from the game data."""
    locations = []
    # Combine home and away pitcher data
    for key in ['home_pitchers', 'away_pitchers']:
        pitcher_group = game_data.get(key, {})
        for pitcher_id, pitches in pitcher_group.items():
            for pitch in pitches:
                if 'px' in pitch and 'pz' in pitch:
                    locations.append({'px': pitch['px'], 'pz': pitch['pz']})
    return locations


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

def extract_current_at_bat_pitch_locations(game_data):
    locations = []
    current_play = fetch_current_play_data(game_data)
    if current_play:
        play_events = current_play.get('playEvents', [])
        for pitch in play_events:
            pitch_data = pitch.get('pitchData', {})
            if pitch_data:
                coordinates = pitch_data.get('coordinates', {})
                if coordinates:
                    px = coordinates.get('pX')
                    pz = coordinates.get('pZ')
                    if px is not None and pz is not None:
                        locations.append({
                            'px': px,
                            'pz': pz,
                            'startSpeed': pitch_data.get('pitch_type'),
                            'endSpeed': pitch_data.get('start_speed'),
                            

                        })
    return locations
    

def extract_pitch_locations_for_pitcher(game_data, pitcher_name):
    """Extracts pitch locations for a specific pitcher by name."""
    locations = []
    # Check both home and away pitchers
    for team in ['home_pitchers', 'away_pitchers']:
        pitchers = game_data.get(team, {})
        for pitcher_id, pitches in pitchers.items():
            if pitches[00]['pitcher_name'].lower().strip() == pitcher_name.lower().strip():  # Compare names in a case-insensitive manner
                for pitch in pitches:
                    if 'px' in pitch and 'pz' in pitch:
                        locations.append({'px': pitch['px'], 'pz': pitch['pz']})

    return locations

def extract_pitch_data_for_pitcher(game_data, pitcher_name):
    """Extracts pitch data for a specific pitcher by name."""
    pitch_data = []
    # Check both home and away pitchers
    for team in ['home_pitchers', 'away_pitchers']:
        pitchers = game_data.get(team, {})
        for pitcher_id, pitches in pitchers.items():
            if pitches[00]['pitcher_name'].lower().strip() == pitcher_name.lower().strip():  # Compare names in a case-insensitive manner
                for pitch in pitches:
                    if 'px' in pitch and 'pz' in pitch:
                        pitch_details = {
                            'px': pitch['px'],
                            'pz': pitch['pz'],
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
                            'pitch_types': pitch.get('pitch_types')
                        }
                        pitch_data.append(pitch_details)
                        
    return pitch_data

def fetch_strike_zone_data(game_data):
    """Extracts strike zone details from game data."""
    # Fetch current play data
    print("Fetching strike zone data...")
    current_play = fetch_current_play_data(game_data)
    play_events = current_play.get('playEvents', [])
    if play_events:
        pitch_data = play_events[0].get('pitchData', {})  # Access the first event's pitch data
        strike_zone_top = pitch_data.get('strikeZoneTop')
        strike_zone_bottom = pitch_data.get('strikeZoneBottom')
        print(f"Strike zone data found: top={strike_zone_top}, bottom={strike_zone_bottom}")
        
        if strike_zone_top is not None and strike_zone_bottom is not None:
            return {'top': strike_zone_top, 'bottom': strike_zone_bottom}
        else:
            print("Strike zone data not found in the first play event.")
    else:
        print("No play events found for the current play.")
    
    # Return default values if the necessary data is not found
    return {'top': 3.5, 'bottom': 1.5}

def fetch_current_play_data(game_data):
    """Extracts current play details from game data."""
    # Navigate to the correct path to extract current play data
    current_play = game_data.get('scoreboard', {}).get('currentPlay', {})
    if current_play:
        print(f"Current play data found: {current_play}")
        return current_play
    else:
        print("No current play data found.")
        return {}

if __name__ == '__main__':
    app.run_server(debug=True)
