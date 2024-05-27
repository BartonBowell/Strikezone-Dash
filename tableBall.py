from dash import dash_table
from dash import dcc
import dash_bootstrap_components as dbc
import numpy as np

#Creates a table for the player stats compared to league and team averages

def create_data_table(player_dict, league_avg_dict, team_avg_dict, table_id):
    columns = [{"name": i, "id": i} for i in player_dict.keys()]
    data = [player_dict, league_avg_dict, team_avg_dict]
    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=data,
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left'},
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'fontWeight': 'bold', 'color': 'white'},
        style_table={'backgroundColor': 'rgb(50, 50, 50)'},
    )


def generate_layout(dataframe):
    # List of columns to exclude from the dropdowns
    columns_to_exclude = ['IDfg', 'Name', 'Events', 'Age Rng']

    # Filter to include only numeric columns and exclude specified columns
    numeric_columns = dataframe.select_dtypes(include=[np.number]).columns.tolist()
    valid_columns = [col for col in numeric_columns if col not in columns_to_exclude]
    dropdown_options = [{'label': col, 'value': col} for col in valid_columns]
    operator_options = [
        {'label': 'Less than', 'value': '<'},
        {'label': 'Less than or equal to', 'value': '<='},
        {'label': 'Equal to', 'value': '='},
        {'label': 'Greater than', 'value': '>'},
        {'label': 'Greater than or equal to', 'value': '>='}
    ]

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.RadioItems(
                    id='data-toggle',
                    options=[{'label': 'qual Player Stats', 'value': 'qual'}, {'label': 'Player Stats', 'value': 'player'}],
                    value='qual'
                ),
                dcc.Checklist(
                    id='invert-x-axis',
                    options=[{'label': 'Invert X Axis', 'value': 'invert'}],
                    value=[]
                ),
                dcc.Checklist(
                    id='invert-y-axis',
                    options=[{'label': 'Invert Y Axis', 'value': 'invert'}],
                    value=[]
                ),
                dcc.Dropdown(
                    id='xaxis-column',
                    options=dropdown_options,
                    value='OBP' if 'OBP' in valid_columns else 'ERA'
                ),
                dcc.Dropdown(
                    id='yaxis-column',
                    options=dropdown_options,
                    value='SLG' if 'SLG' in valid_columns else 'WHIP'
                ),
                dcc.Dropdown(
                    id='qualifier-column',
                    options=dropdown_options,
                    value='OBP' if 'OBP' in valid_columns else 'WHIP'
                ),
                dcc.Dropdown(
                    id='comparison-operator',
                    options=operator_options,
                    value='>='
                ),
                dcc.Input(
                    id='qualifier-value',
                    type='number',
                    value=0
                ),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=[{'label': i, 'value': i} for i in range(1900, 2025)],
                    value=2022
                ),
                dcc.Dropdown(
                    id='end-year-dropdown',
                    options=[{'label': i, 'value': i} for i in range(1900, 2025)],
                    value=2024
                ),
                dcc.Checklist(
    id='team-toggle',
    options=[{'label': 'Display Team Data', 'value': 'TEAM_DATA'}],
    value=[]
),
                dcc.Checklist(
                    id='name-toggle',
                    options=[{'label': 'Show names', 'value': 'SHOW_NAMES'}],
                    value=['SHOW_NAMES']
                ),dcc.Checklist(
    id='ind-toggle',
    options=[
        {'label': 'Aggregate Data', 'value': '0'}  # If checked, '0' will be passed as ind
    ],
    value=['0']  # Default to aggregated stats; remove '0' to default to individual stats
)
            ], xs=12, sm=12, md=4, lg=3, xl=3),
            dbc.Col([
                dcc.Graph(
    id='scatter-plot', 
    style={'height': '1100px', 'width': '1100px'},
    config={
        'displayModeBar': False,
        'responsive': True
    },
    figure={
        'layout': {
            'autosize': False,
            'width': 1100,
            'height': 1100,
            'xaxis': {
                'range': [0, 5],
                'scaleanchor': 'y',
                'scaleratio': 1,
            },
            'yaxis': {
                'range': [0, 5],
            },
            'legend': {
                'x': 0.5,
                'y': -0.1,
                'xanchor': 'center'
            }
        }
    }
)
            ], xs=12, sm=12, md=8, lg=9, xl=9)
        ])
    ], fluid=True)
# Define index page layout

def create_events_table(events):
    columns = [{"name": i, "id": i} for i in events[0].keys()] if events else []
    return dash_table.DataTable(
        id='recent-events-table',
        columns=columns,
        data=events,
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left'},
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'fontWeight': 'bold', 'color': 'white'},
        style_table={'backgroundColor': 'rgb(50, 50, 50)', 'height': '17.5vh', 'width': '95%', 'overflowY': 'auto', 'margin': 'auto'},
        css=[{
            'selector': '::-webkit-scrollbar',
            'rule': 'display: none;'
        }, {
            'selector': '::-webkit-scrollbar {width: 0px; height: 0px;}', 
            'rule': ''
        }, {
            'selector': '::-webkit-scrollbar-thumb {background-color: transparent;}', 
            'rule': ''
        }, {
            'selector': '::-webkit-scrollbar-track {background-color: transparent;}', 
            'rule': ''
        }, {
            'selector': 'scrollbar-width',
            'rule': 'none;'
        }]
    )
def create_events_table(events):
    if events:
        # Sort events by 'Pitch #' before creating the table
        events.sort(key=lambda x: x['Pitch #'],reverse=True)
        # Exclude 'Pitch #' from the columns list
        columns = [{"name": i, "id": i} for i in events[0].keys() if i != 'Pitch #']
    else:
        columns = []

    return dash_table.DataTable(
        id='recent-events-table',
        columns=columns,
        data=events,
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left', 'maxWidth': '150px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'fontWeight': 'bold', 'color': 'white'},
        style_table={'backgroundColor': 'rgb(50, 50, 50)', 'height': '17.5vh', 'width': '95%', 'overflowY': 'auto', 'margin': 'auto'},
        css=[{
            'selector': '.data-table-container ::-webkit-scrollbar',
            'rule': 'display: none;'
        }, {
            'selector': '.data-table-container ::-webkit-scrollbar-thumb',
            'rule': 'background-color: transparent;'
        }, {
            'selector': '.data-table-container ::-webkit-scrollbar-track',
            'rule': 'background-color: transparent;'
        }, {
            'selector': '.data-table-container',
            'rule': 'scrollbar-width: none; -ms-overflow-style: none;'
        }]
    )
