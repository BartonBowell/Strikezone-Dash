import dash
from dash import dcc, html,dash_table
import dash_bootstrap_components as dbc
import plotly.io as pio
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import numpy as py
import pandas as pd
import pybaseball
import dataBall, fetchBall, tableBall, stadiumBall, runnerBall

pio.templates.default = "plotly_dark"

############### DASH APP / HTML LAYOUT ###############

pybaseball.cache.enable()
app = dash.Dash(__name__, external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.layout = html.Div([
    dcc.Store(id='game-data-store', storage_type='memory'),
    dcc.Interval(id='page-load', interval=1*100, max_intervals=1),
    html.Div([
        dcc.Input(id='gamepk-input', type='text', placeholder='Enter Game PK', style={'display': 'none'}),
        dcc.Input(id='pitcher-name-input', type='text', placeholder='Enter Pitcher Name', style={'display': 'none'}),
        html.Div([
            html.Button('Fetch Data', style={'display': 'none'}, id='fetch-button', n_clicks=0),
            dcc.Dropdown(
                id='pitcher-dropdown',
                options=[],  # This will be populated dynamically
                placeholder='Select a pitcher',
                style={'width': '45%', 'margin': '10px'}
            ),
            dcc.Dropdown(
                id='gamepk-dropdown',
                options=[],  # This will be populated dynamically
                placeholder='Select a gamepk',
                style={'width': '45%', 'margin': '10px'}
            )
        ], style={'display': 'flex', 'justifyContent': 'space-around'}),
        dcc.Interval(id='interval-component', interval=12*1000, n_intervals=0)
    ], style={'text-align': 'center'}),
    html.Div([
        html.Div([
            dcc.Graph(id='strike-zone-graph', style={'width': '80%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '25%', 'padding': '0', 'margin': '0'}),
        html.Div([
            dcc.Graph(id='current-zone-graph', style={'width': '80%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '25%', 'padding': '0', 'margin': '0'}),
        html.Div([
            dcc.Graph(id='win-probability-graph', style={'width': '100%', 'margin': '0', 'padding': '0'})
        ], style={'display': 'inline-block', 'width': '25%', 'padding': '0', 'margin': '0'}),
        html.Div([
            dcc.Graph(id='stadium-plot', style={'height': '50vh', 'width': '100%', 'margin': '0'}),
        ], style={'display': 'inline-block', 'width': '25%', 'padding': '0', 'margin': '0'})
    ], style={'width': '100%', 'padding': '0', 'margin': '0', 'backgroundColor': '#111111'}),
    html.Div([
        html.Div(id='pitcher-table-container', style={'flex': '1', 'padding': '10px'}),
        html.Div(id='batter-table-container', style={'flex': '1', 'padding': '10px'}),
        html.Div(id='recent-events-container', style={'flex': '1', 'padding': '10px'})
    ], style={'display': 'flex', 'justify-content': 'space-around', 'align-items': 'center', 'backgroundColor': '#111111'}),
    html.Div([
        dcc.Graph(
            id='live-pitch-data-graph', 
            style={'height': '40vh', 'width': '100%', 'margin': '0'},
            figure={
                'layout': {
                    'paper_bgcolor': 'rgba(0, 0, 0, 0)', 
                    'plot_bgcolor': 'rgba(0, 0, 0, 0)', 
                    'font': {'color': 'white'}
                }
            },
            config={}
        ),
    ]),
    html.Div([
        html.Div([
            html.H2('Home Batting Stats'),
            dash_table.DataTable(id='home-batting-stats-table', style_cell={'width': '100px'})
        ], style={'flex': '50%'}),
        html.Div([
            html.H2('Away Batting Stats'),
            dash_table.DataTable(id='away-batting-stats-table', style_cell={'width': '100px'})
        ], style={'flex': '50%'}),
    ], id='team-stats-container', style={'display': 'flex', 'backgroundColor': '#111111'}),
    html.Div([
        dcc.Checklist(
            id='toggle-labels',
            options=[{'label': 'Show Labels', 'value': 'show'}],
            value=[],
            style={'display': 'inline-block'}
        )
    ])
], style={'backgroundColor': '#111111'})
    

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


@app.callback(
    [Output('home-batting-stats-table', 'data'),
     Output('home-batting-stats-table', 'columns'),
     Output('home-batting-stats-table', 'style_cell'),
     Output('home-batting-stats-table', 'style_header'),
     Output('home-batting-stats-table', 'style_data'),
     Output('home-batting-stats-table', 'style_table')],
    [Input('gamepk-dropdown', 'value'), Input('game-data-store', 'data')]
)
def update_home_batting_stats(gamepk, data):
    game_data = data['game_data'] if data else None
    if gamepk:
        home_win_probs, away_win_probs, home_team, away_team = dataBall.extract_win_probabilities(game_data)
        team_replacements = {'AZ': 'ARI', 'WSH': 'WSN', 'TB': 'TBR', 'CWS': 'CHW', 'SF': 'SFG', 'SD': 'SDP', 'KC': 'KCR'}
        for old, new in team_replacements.items():
            home_team = home_team.replace(old, new)
        home_batting_stats = dataBall.extract_team_player_stats(home_team)
        df = pd.DataFrame.from_dict(home_batting_stats, orient='index')
        df.reset_index(inplace=True)
        df.columns = ['Player'] + [col for col in df.columns[1:]]  # Assuming the first column is 'Player'
        return df.to_dict('records'), [{"name": str(i), "id": str(i)} for i in df.columns], {'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left', 'minWidth': '25px', 'width': '25px'}, {'backgroundColor': 'rgb(30, 30, 30)', 'fontWeight': 'bold', 'color': 'white'}, {'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'}, { 'width': '95%', 'overflowY': 'auto', 'margin': 'auto'}
    return [], [], {}, {}, {}, {}

@app.callback(
    [Output('away-batting-stats-table', 'data'),
     Output('away-batting-stats-table', 'columns'),
     Output('away-batting-stats-table', 'style_cell'),
     Output('away-batting-stats-table', 'style_header'),
     Output('away-batting-stats-table', 'style_data'),
     Output('away-batting-stats-table', 'style_table')],
    [Input('gamepk-dropdown', 'value'), Input('game-data-store', 'data')]
)
def update_away_batting_stats(gamepk, data):
    game_data = data['game_data'] if data else None
    if gamepk:
        home_win_probs, away_win_probs, home_team, away_team = dataBall.extract_win_probabilities(game_data)
        team_replacements = {'AZ': 'ARI', 'WSH': 'WSN', 'TB': 'TBR', 'CWS': 'CHW', 'SF': 'SFG', 'SD': 'SDP', 'KC': 'KCR'}
        for old, new in team_replacements.items():
            away_team = away_team.replace(old, new)
        away_batting_stats = dataBall.extract_team_player_stats(away_team)
        df = pd.DataFrame.from_dict(away_batting_stats, orient='index')
        df.reset_index(inplace=True)
        df.columns = ['Player'] + [col for col in df.columns[1:]]  # Assuming the first column is 'Player'
        return df.to_dict('records'), [{"name": str(i), "id": str(i)} for i in df.columns], {'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left', 'minWidth': '25px', 'width': '25px'}, {'backgroundColor': 'rgb(30, 30, 30)', 'fontWeight': 'bold', 'color': 'white'}, {'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'}, { 'width': '95%', 'overflowY': 'auto', 'margin': 'auto'}
    return [], [], {}, {}, {}, {}

#############Data Storage################
# Fetch game data
@app.callback(
    Output('game-data-store', 'data'),
    [Input('interval-component', 'n_intervals'),
     Input('page-load', 'n_intervals'),
     Input('gamepk-dropdown', 'value')],  # Listen to 'gamepk-dropdown.value'
    [State('game-data-store', 'data')]
)
def fetch_game_data(n_intervals, page_load, game_pk, stored_data):
    if n_intervals > 0 or page_load == 1 or game_pk:  # Fetch data if the interval component has completed an interval, the page has loaded, or a new gamepk is selected
        game_data = fetchBall.fetch_game_data(game_pk)
        strike_zone_data = fetchBall.fetch_strike_zone_data(game_data) if game_data else None
        return {'game_data': game_data, 'strike_zone_data': strike_zone_data}
    return stored_data  # Return the stored data if no inputs triggered the callback

@app.callback(
    [Output('pitcher-dropdown', 'options'),
     Output('pitcher-dropdown', 'value')],
    [Input('game-data-store', 'data')],
    [State('pitcher-dropdown', 'value')]
)
def update_pitcher_dropdown(data, current_value):
    if data:
        game_data = data['game_data']
        pitcher_names = dataBall.extract_pitcher_names(game_data)
        options = [{'label': name, 'value': name} for name in pitcher_names]
        # If the current value is in the options list, keep it. Otherwise, set the value to the top option
        value = current_value if current_value in pitcher_names else options[0]['value'] if options else None
        return options, value
    return [], None

@app.callback(
    [Output('gamepk-dropdown', 'options'),
     Output('gamepk-dropdown', 'value')],
    [Input('interval-component', 'n_intervals'),
     Input('page-load', 'n_intervals')],  # Add 'page-load' as an input
    [State('gamepk-dropdown', 'value')]
)
def update_gamepk_dropdown(n_intervals, page_load, current_value):
    if n_intervals > 0 or page_load == 1:  # Update if the interval component has completed an interval or the page has loaded
        game_info = fetchBall.get_game_pks_and_teams()
        options = [{'label': f"{info[1]} vs {info[2]}", 'value': info[0]} for info in game_info]
        return options, options[0]['value'] if options and current_value is None else current_value
    return [], None

@app.callback(
    Output('stadium-plot', 'figure'),
    [Input('game-data-store', 'data'),
     Input('gamepk-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]  # Listen to 'interval-component.n_intervals'
)
def update_plot(stored_data, game_pk, n):
    if stored_data and 'game_data' in stored_data:
        runners = runnerBall.get_base_runners(stored_data['game_data'])
        defenders = runnerBall.get_defenders(stored_data['game_data'])
        return stadiumBall.plot_stadium(stored_data['game_data']['home_team_data']['teamName'].lower(), runners=runners,defenders=defenders, title='')
    else:
        return go.Figure()  # Return an empty figure if there's no data
##########Pitcher Name Input##############

@app.callback(
    Output('pitcher-name-input', 'value'),
    Input('pitcher-dropdown', 'value')
)
def update_pitcher_name_input(selected_pitcher):
    return selected_pitcher or ''

##########Pitcher Drop Down Menu###########









############


#############Stat/Event Tables###############

@app.callback(
    [Output('pitcher-table-container', 'children'),
     Output('batter-table-container', 'children'),
     Output('recent-events-container', 'children')],
    [Input('game-data-store', 'data'),
     Input('pitcher-dropdown', 'value')]
)
def update_stat_table(stored_data, selected_pitcher_name):
    if stored_data:
        game_data = stored_data['game_data']
        current_play_data = fetchBall.fetch_current_play_data(game_data)

        # Extract batter's full name
        batter_name = current_play_data.get('matchup', {}).get('batter', {}).get('fullName', 'Unknown')

        # Use the selected pitcher's name from the dropdown
        pitcher_name = selected_pitcher_name

        # Fetch and process stats for batter and pitcher
        batter_player_dict, batter_league_average_dict, batter_team_average_dict = dataBall.extract_batter_statline(batter_name)
        pitcher_player_dict, pitcher_league_average_dict, pitcher_team_average_dict = dataBall.extract_pitch_statline(pitcher_name)

        if isinstance(batter_player_dict, str) or isinstance(pitcher_player_dict, str):  # If no stats were found
            return [], [], []

        # Fetch and sort the pitching events
        all_pitching_events = dataBall.extract_all_game_pitching_events(game_data)
        sorted_events = sorted(all_pitching_events, key=lambda x: x['Pitch #'], reverse=True)
        recent_events = sorted_events  # Get the three most recent events

        # Create tables for batter, pitcher, and recent events
        batter_table = tableBall.create_data_table(batter_player_dict, batter_league_average_dict, batter_team_average_dict, 'batter-slashline-table')
        pitcher_table = tableBall.create_data_table(pitcher_player_dict, pitcher_league_average_dict, pitcher_team_average_dict, 'pitcher-slashline-table')
        events_table = tableBall.create_events_table(recent_events)

        return [pitcher_table], [batter_table], [events_table]

    return [], [], []

#######Current AB Zone Graph#################

@app.callback(
    Output('current-zone-graph', 'figure'),
    [Input('game-data-store', 'data')]
)
def update_current_zone(stored_data):
    if stored_data:
        game_data = stored_data['game_data']
        strike_zone_data = stored_data['strike_zone_data']
        if game_data and strike_zone_data:
            current_play_data = fetchBall.fetch_current_play_data(game_data)

            # Extract batter's and pitcher's full name
            batter_name = current_play_data.get('matchup', {}).get('batter', {}).get('fullName', 'Unknown')
            pitcher_name = current_play_data.get('matchup', {}).get('pitcher', {}).get('fullName', 'Unknown')

            # Rest of your code
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
    [Input('game-data-store', 'data'),
     Input('pitcher-dropdown', 'value')]
)
def update_strike_zone(stored_data, pitcher_name):
    if stored_data and pitcher_name:
        game_data = stored_data['game_data']
        strike_zone_data = stored_data['strike_zone_data']
        if game_data and strike_zone_data:
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
                team_colors = {
    'AZ': '#A71930',  # Arizona Diamondbacks
    'ATL': '#CE1141',  # Atlanta Braves
    'BAL': '#DF4601',  # Baltimore Orioles
    'BOS': '#BD3039',  # Boston Red Sox
    'CHC': '#0E3386',  # Chicago Cubs
    'CWS': '#27251F',  # Chicago White Sox
    'CIN': '#C6011F',  # Cincinnati Reds
    'CLE': '#E31937',  # Cleveland Guardians (previously Indians)
    'COL': '#33006F',  # Colorado Rockies
    'DET': '#0C2340',  # Detroit Tigers
    'HOU': '#002D62',  # Houston Astros
    'KCR': '#004687',  # Kansas City Royals
    'LAA': '#BA0021',  # Los Angeles Angels (more red than blue)
    'LAD': '#005A9C',  # Los Angeles Dodgers
    'MIA': '#00A3E0',  # Miami Marlins
    'MIL': '#FFC52F',  # Milwaukee Brewers (added gold color)
    'MN': '#002B5C',  # Minnesota Twins
    'NYM': '#002D72',  # New York Mets
    'NYY': '#003087',  # New York Yankees
    'OAK': '#003831',  # Oakland Athletics
    'PHI': '#E81828',  # Philadelphia Phillies
    'PIT': '#FDB827',  # Pittsburgh Pirates (added yellow color)
    'SD': '#2F241D',  # San Diego Padres
    'SF': '#FD5A1E',  # San Francisco Giants
    'SEA': '#0C2C56',  # Seattle Mariners
    'STL': '#C41E3A',  # St. Louis Cardinals
    'TBR': '#00285D',  # Tampa Bay Rays
    'TEX': '#003278',  # Texas Rangers
    'TOR': '#134A8E',  # Toronto Blue Jays
    'WSH': '#AB0003'   # Washington Nationals
}

                add_trace(fig, list(range(len(home_win_probs))), home_win_probs, 'lines', home_team, None, 'y1', None, dict(color=team_colors.get(home_team, 'black')))

                add_trace(fig, list(range(len(away_win_probs))), away_win_probs, 'lines', away_team, None, 'y1', None, dict(color=team_colors.get(away_team, 'black')))
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
     Input('toggle-labels', 'value'),  # This takes the state of the checkbox
     Input('pitcher-dropdown', 'value')],  # Listen to 'pitcher-dropdown.value'
    [State('gamepk-dropdown', 'value')]
)
def update_graph_live(button_clicks, n_intervals, toggle_labels, pitcher_name, game_id):

    if not game_id or not pitcher_name:
        return go.Figure()

    game_data = fetchBall.fetch_game_data(game_id)

    if game_data:
        pitching_events = dataBall.extract_pitching_events(game_data) 
        pitch_data_df = pd.DataFrame(pitching_events)
        filtered_data = pitch_data_df[pitch_data_df['pitcher_name'] == pitcher_name]
    else:
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
