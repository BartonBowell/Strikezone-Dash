import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import requests
import json
import pandas as pd

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
        dcc.Graph(id='strike-zone-graph', style={'height': '50vh', 'width': '100%', 'margin': '0'})
    ]),
    html.Div([
        dcc.Graph(id='live-pitch-data-graph', style={'height': '50vh', 'width': '100%', 'margin': '0'})
    ])
])
# Callback for the strike zone graph
@app.callback(
    Output('strike-zone-graph', 'figure'),
    [Input('fetch-button', 'n_clicks')],
    [State('gamepk-input', 'value'), State('pitcher-name-input', 'value')]
)
def update_strike_zone(n_clicks, game_pk, pitcher_name):
    if n_clicks > 0 and game_pk:
        game_data = fetch_game_data(game_pk)
        if game_data and pitcher_name:
            strike_zone_data = fetch_strike_zone_data(game_data)
            pitch_locations = extract_pitch_locations_for_pitcher(game_data, pitcher_name)

            fig = go.Figure()

            # Draw the strike zone
            fig.add_shape(type="rect",
                          x0=-0.7083, y0=strike_zone_data['bottom'],
                          x1=0.7083, y1=strike_zone_data['top'],
                          line=dict(color="RoyalBlue"))

            # Plot each pitch location with increased marker size
            for location in pitch_locations:
                fig.add_trace(go.Scatter(
                    x=[location['px']],
                    y=[location['pz']],
                    mode='markers',
                    marker=dict(color='red', size=15),
                    name='Pitch Location'
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
    return go.Figure()


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


def fetch_strike_zone_data(game_pk):
    """Fetches game data from Baseball Savant and extracts strike zone details."""
    url = f"https://baseballsavant.mlb.com/gf?game_pk={game_pk}"
    response = requests.get(url)
    if response.status_code == 200:
        game_data = response.json()
        # Navigate to the correct path to extract strike zone data
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
    else:
        print("Failed to fetch data:", response.status_code)
    
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
        text_labels = filtered_data.apply(lambda x: f"Pitch Type: {x['pitch_type']}<br>" +
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
        text_labels = filtered_data.apply(lambda x: f"Pitch Type: {x['pitch_type']}<br>" +
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
