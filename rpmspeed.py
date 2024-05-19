import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import requests

app = dash.Dash(__name__)

# Define the layout of the application
app.layout = html.Div([
    html.H1("Live Pitch Data Visualization", style={'textAlign': 'center'}),
    html.Div([
        dcc.Input(id='input-gamepk', type='text', placeholder='Enter Game PK', style={'marginRight': '10px'}),
        dcc.Input(id='input-pitcher-name', type='text', placeholder='Enter Pitcher Name'),
        html.Button('Update Data', id='submit-button', n_clicks=0),
    ], style={'marginBottom': '20px'}),
    dcc.Graph(
        id='live-update-graph',
        style={'width': '100%', 'height': '90vh'}  # Use 90% of the viewport height
    ),
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # in milliseconds, updates every 30 seconds
        n_intervals=0
    )
], style={'padding': '10px', 'margin': '0px'})

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
