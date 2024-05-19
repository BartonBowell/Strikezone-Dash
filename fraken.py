import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import requests
import json
import pandas as pd
import seaborn as sns

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1("Baseball Pitch Data Visualization", style={'text-align': 'center'}),
    html.Div([
        dcc.Input(id='gamepk-input', type='text', placeholder='Enter Game PK', style={'marginRight': '10px'}),
        dcc.Input(id='pitcher-name-input', type='text', placeholder='Enter Pitcher Name', style={'marginRight': '10px'}),
        html.Button('Fetch Data', id='fetch-button', n_clicks=0),
        dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0)
    ], style={'text-align': 'center', 'padding': '10px'}),
    html.Div([
        html.Div([
            dcc.Graph(id='strike-zone-graph', style={'height': '50vh', 'width': '100%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '50%', 'padding': '0', 'margin': '0'}),
        html.Div([
            dcc.Graph(id='current-zone-graph', style={'height': '50vh', 'width': '100%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '50%', 'padding': '0', 'margin': '0'})
    ], style={'width': '100%', 'padding': '0', 'margin': '0'}),
    html.Div([
        dcc.Graph(id='live-pitch-data-graph', style={'height': '50vh', 'width': '100%', 'margin': '0'})
    ])
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
            pitch_locations = extract_pitch_data_for_pitcher(game_data, pitcher_name)

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
                fig.add_trace(go.Scatter(
                    x=[location['px']],
                    y=[location['pz']],
                    mode='markers',
                    marker=dict(color=color_map[location['pitch_type']], size=15),
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
                    px = coordinates.get('pX')
                    pz = coordinates.get('pZ')

                    # Plot the pitch location
                    fig.add_trace(go.Scatter(
                        x=[px],
                        y=[pz],
                        mode='markers',
                        marker=dict(color='red', size=15),
                        name='Pitch Location',
                        hovertemplate=f"px: {px}, pz: {pz}"
                    ))

                # Set figure properties
                fig.update_layout(
                    title=f"Strike Zone with Current Pitch Location for {batter_name}",  # Update the title with the batter's name
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


@app.callback(
    Output('live-pitch-data-graph', 'figure'),
    [Input('fetch-button', 'n_clicks'), Input('interval-component', 'n_intervals')],
    [State('gamepk-input', 'value'), State('pitcher-name-input', 'value')]
)
def update_graph_live(button_clicks, n_intervals, game_id, pitcher_name):
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
                            'pitch_type': pitch_data.get('pitch_type'),
                            'start_speed': pitch_data.get('start_speed'),
                            'end_speed': pitch_data.get('end_speed'),
                            'spin_rate': pitch_data.get('spin_rate'),
                            'result': pitch_data.get('result'),
                            'description': pitch_data.get('des'),
                            'call': pitch_data.get('call_name'),
                            'batter_name': pitch_data.get('batter_name'),
                            'ab_number': pitch_data.get('ab_number'),
                            'pitch_name': pitch_data.get('pitch_name'),
                            'pitch_types': pitch_data.get('pitch_types')
                        })
    return locations

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

class PitchData:
    def __init__(self, game_id, pitcher_name):
        self.game_id = game_id
        self.pitcher_name = pitcher_name

    def fetch_game_data_from_savant(self):
        url = f"https://baseballsavant.mlb.com/gf?game_pk={self.game_id}"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None

    def get_filtered_data(self):
        game_data = self.fetch_game_data_from_savant()
        if game_data:
            pitching_events = self.extract_pitching_events(game_data)
            return self.filter_pitch_data(pitching_events)
        else:
            print(f"Error fetching data for game {self.game_id}")
            return pd.DataFrame()

    def extract_pitching_events(self, game_data):
        pitching_events = []
        try:
            pitch_velocity_data = game_data.get('away_pitchers', {}) | game_data.get('home_pitchers', {})
            for pitcher_id, pitcher_data in pitch_velocity_data.items():
                for pitch in pitcher_data:
                    pitch_details = {
                        "pitch_type": pitch.get("pitch_type"),
                        "pitch_name": pitch.get("pitch_name"),
                        "start_speed": pitch.get("start_speed"),
                        "end_speed": pitch.get("end_speed"),
                        "spin_rate": pitch.get("spin_rate"),
                        "pitcher_name": pitch.get("pitcher_name"),
                        "result": pitch.get("result"),
                        "description": pitch.get("des"),
                        "call": pitch.get("call_name"),
                        "batter_name": pitch.get("batter_name")
                    }
                    pitching_events.append(pitch_details)
        except KeyError as e:
            print(f"KeyError: {e}")
        return pitching_events

    def filter_pitch_data(self, pitch_data):
        pitch_data_df = pd.DataFrame(pitch_data)
        return pitch_data_df[(pitch_data_df['pitcher_name'] == self.pitcher_name)]

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

if __name__ == '__main__':
    app.run_server(debug=True)
