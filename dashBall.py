import dash
from dash import dcc, html,dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import numpy as py
import pandas as pd
import pybaseball
import dataBall
import fetchBall
import tableBall


############### DASH APP / HTML LAYOUT ###############

pybaseball.cache.enable()
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Store(id='game-data-store', storage_type='memory'),
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
       
        dcc.Interval(id='interval-component', interval=12*1000, n_intervals=0)
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
    html.Div(id='pitcher-table-container', style={'flex': '1', 'padding': '10px'}),
    html.Div(id='batter-table-container', style={'flex': '1', 'padding': '10px'}),
    html.Div(id='recent-events-container', style={'flex': '1', 'padding': '10px'})
], style={'display': 'flex', 'justify-content': 'space-around', 'align-items': 'center'})
,html.Div([
        dcc.Graph(id='live-pitch-data-graph', style={'height': '40vh', 'width': '100%', 'margin': '0'})
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

############### CALLBACKS ###############

#############Data Storage################
@app.callback(
    Output('game-data-store', 'data'),
    [Input('fetch-button', 'n_clicks')],
    [State('gamepk-input', 'value')]
)
def fetch_game_data(n_clicks, game_pk):
    if n_clicks > 0 and game_pk:
        game_data = fetchBall.fetch_game_data(game_pk)
        strike_zone_data = fetchBall.fetch_strike_zone_data(game_data) if game_data else None
        return {'game_data': game_data, 'strike_zone_data': strike_zone_data}
    return {}

##########Pitcher Name Input##############

@app.callback(
    Output('pitcher-name-input', 'value'),
    Input('pitcher-dropdown', 'value')
)
def update_pitcher_name_input(selected_pitcher):
    return selected_pitcher or ''

##########Pitcher Drop Down Menu###########

@app.callback(
    Output('pitcher-dropdown', 'options'),
    Input('game-data-store', 'data')
)
def update_pitcher_dropdown(stored_data):
    if stored_data:
        game_data = stored_data['game_data']
        pitcher_names = dataBall.extract_pitcher_names(game_data)
        options = [{'label': name, 'value': name} for name in pitcher_names]
        return options
    return []

#############Stat/Event Tables###############

@app.callback(
    Output('pitcher-table-container', 'children'),
    Output('batter-table-container', 'children'),
    Output('recent-events-container', 'children'),
    Input('game-data-store', 'data'),
    State('pitcher-name-input', 'value')
)
def update_stat_table(stored_data, current_pitcher_name):
    if stored_data:
        game_data = stored_data['game_data']
        current_play_data = fetchBall.fetch_current_play_data(game_data)

        # Extract batter's and pitcher's full name
        batter_name = current_play_data.get('matchup', {}).get('batter', {}).get('fullName', 'Unknown')
        pitcher_name = current_play_data.get('matchup', {}).get('pitcher', {}).get('fullName', 'Unknown')

        # Fetch and process stats for batter and pitcher
        batter_player_dict, batter_league_average_dict, batter_team_average_dict = dataBall.extract_batter_statline(batter_name)
        pitcher_player_dict, pitcher_league_average_dict, pitcher_team_average_dict = dataBall.extract_pitch_statline(pitcher_name)

        if isinstance(batter_player_dict, str) or isinstance(pitcher_player_dict, str):  # If no stats were found
            return [], [], []

        # Fetch and sort the pitching events
        all_pitching_events = dataBall.extract_all_game_pitching_events(game_data)
        sorted_events = sorted(all_pitching_events, key=lambda x: x['Pitch #'], reverse=True)
        recent_events = sorted_events[:4]  # Get the three most recent events

        # Create tables for batter, pitcher, and recent events
        batter_table = tableBall.create_data_table(batter_player_dict, batter_league_average_dict, batter_team_average_dict, 'batter-slashline-table')
        pitcher_table = tableBall.create_data_table(pitcher_player_dict, pitcher_league_average_dict, pitcher_team_average_dict, 'pitcher-slashline-table')
        events_table = tableBall.create_events_table(recent_events)

        return [pitcher_table], [batter_table], [events_table]

    return [], [], []

#######Current AB Zone Graph#################

@app.callback(
    Output('current-zone-graph', 'figure'),
    [Input('game-data-store', 'data')],
    [State('pitcher-name-input', 'value')]
)
def update_current_zone(stored_data, pitcher_name):
    if stored_data:
        game_data = stored_data['game_data']
        strike_zone_data = stored_data['strike_zone_data']
        if game_data and strike_zone_data and pitcher_name:
            current_play_data = fetchBall.fetch_current_play_data(game_data)

            # Extract batter's full name
            batter_name = current_play_data.get('matchup', {}).get('batter', {}).get('fullName', 'Unknown')
            pitcher_name = current_play_data.get('matchup', {}).get('pitcher', {}).get('fullName', 'Unknown')

            # Check if playEvents is a list
            if isinstance(current_play_data.get('playEvents'), list):
                fig = go.Figure()
                draw_strike_zone(fig, strike_zone_data)

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

                    add_trace(fig, [px], [pz], 'markers', pitch_type, None, 'y1', 
          dict(color=color, size=15), None, 
          f"Type: {pitch_type}<br>Speed: {pitch_speed} mph<br>Spin rate: {spin_rate}<br>Count: {count}<br>Call: {call}<br>Batter: {batter_name}")

                # Set figure properties
                set_figure_layout(fig, f"Current Pitch Location for {pitcher_name}<br>Current Batter {batter_name}", "Width (feet)", "Height (feet)")
                return fig
    return go.Figure()  # Return an empty figure if no data

#########Cumulative Zone Graph##################

@app.callback(
    Output('strike-zone-graph', 'figure'),
    [Input('game-data-store', 'data')],
    [State('pitcher-name-input', 'value')]
)
def update_strike_zone(stored_data, pitcher_name):
    if stored_data:
        game_data = stored_data['game_data']
        strike_zone_data = stored_data['strike_zone_data']
        if game_data and strike_zone_data and pitcher_name:
            pitch_locations = dataBall.get_pitcher_data(game_data, pitcher_name)
            
            fig = go.Figure()
            draw_strike_zone(fig, strike_zone_data)

            # Plot each pitch location
            for location in pitch_locations:
                add_trace(fig, [location['px']], [location['pz']], 'markers+text', None, None, 'y1', 
          dict(color=color_dict.get(location['pitch_name'], 'black'), size=15), None, 
          f"<br>Speed: {location['start_speed']} mph<br>Result: {location['result']}<br>Spin Rate: {location['spin_rate']} rpm<br>Call: {location['call']}<br>Result: {location['result']}<br>Batter: {location['batter_name']}<br>Inning: {location['inning']}<br>Pitch Type: {location['pitch_name']}")

            # Set figure properties
            set_figure_layout(fig, "Strike Zone with All Pitch Locations", "Width (feet)", "Height (feet)")
            return fig
    return go.Figure()  # Return an empty figure if no data

#########Win Probability Graph#################

@app.callback(
    Output('win-probability-graph', 'figure'),
    Input('game-data-store', 'data')
)
def update_win_probability_graph(stored_data):
    if stored_data:
        game_data = stored_data['game_data']
        previous_result = dataBall.extract_current_result(game_data)
        if game_data:
            home_win_probs, away_win_probs, home_team, away_team = dataBall.extract_win_probabilities(game_data)

            if home_win_probs is not None and away_win_probs is not None:
                fig = go.Figure()

                add_trace(fig, list(range(len(home_win_probs))), home_win_probs, 'lines', home_team, None, 'y1', None, dict(color='blue'))

                add_trace(fig, list(range(len(away_win_probs))), away_win_probs, 'lines', away_team, None, 'y1', None, dict(color='red'))

                # Check if previous_result is None
                if previous_result is None:
                    previous_result = 'No current at bat'

                fig.update_layout(
                title=home_team+" vs "+away_team+ " Win Probability<br>Previous Result: "+previous_result,
                yaxis_title="Win Probability",
                xaxis_title="Time",
                showlegend=True,
                xaxis=dict(range=[0, None])  # Set the minimum of x-axis to 0 and maximum to auto range
            )

                return fig

    return go.Figure()  # Return an empty figure if no data

#############Speed/Spinrate Graph##################

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

    game_data = fetchBall.fetch_game_data(game_id)
    if game_data:
        pitching_events = dataBall.extract_pitching_events(game_data) 
        pitch_data_df = pd.DataFrame(pitching_events)
        filtered_data = pitch_data_df[pitch_data_df['pitcher_name'] == pitcher_name]
    else:
        print(f"Error fetching data for game {game_id}")
        filtered_data = pd.DataFrame()

    fig = go.Figure()
    if not filtered_data.empty:  # Check if the DataFrame is not empty
        mode = 'markers+lines+text' if toggle_labels else 'markers+lines'  # Decide whether to include text based on toggle_labels
        add_trace(fig, list(range(len(filtered_data))), filtered_data['start_speed'], mode, 'Pitch Speed', 
          filtered_data.apply(lambda x: f"{x['pitch_name']}: {x['start_speed']} mph", axis=1))

        add_trace(fig, list(range(len(filtered_data))), filtered_data['spin_rate'], mode, 'Spin Rate', 
          filtered_data.apply(lambda x: f"{x['pitch_name']}: {x['spin_rate']} rpm", axis=1), 'y2')
        
        fig.update_layout(
            yaxis=dict(title='Start Speed (mph)'),
            yaxis2=dict(title='Spin Rate (rpm)', overlaying='y', side='right')
        )
        fig.update_layout(transition={'duration': 500})

    return fig

#########Callback Functions################

def add_trace(fig, x_data, y_data, mode, name, text_data=None, yaxis='y1', marker_dict=None, line_dict=None, hovertemplate=None):
    trace = go.Scatter(
        x=x_data,
        y=y_data,
        mode=mode,
        name=name,
        yaxis=yaxis
    )
    if text_data is not None:
        trace['text'] = text_data
        trace['textposition'] = 'top center'
        trace['hoverinfo'] = 'text'
        trace['hovertemplate'] = '%{text}<extra></extra>'
    if marker_dict is not None:
        trace['marker'] = marker_dict
    if line_dict is not None:
        trace['line'] = line_dict
    if hovertemplate is not None:
        trace['hovertemplate'] = hovertemplate
    fig.add_trace(trace)

    
def draw_strike_zone(fig, strike_zone_data):
    """ Add a rectangle for the strike zone to a figure. """
    fig.add_shape(type="rect",
                  x0=-0.7083, y0=strike_zone_data['bottom'],
                  x1=0.7083, y1=strike_zone_data['top'],
                  line=dict(color="RoyalBlue"))


def set_figure_layout(fig, title, xaxis_title, yaxis_title):
    """ Set layout properties for the figure. """
    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        showlegend=False,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[0, 5], scaleratio=1),
        xaxis_range=[-2.5, 2.5]
    )


if __name__ == '__main__':
    app.run_server(debug=True)
