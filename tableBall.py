from dash import dash_table

#Creates a table for the player stats compared to league and team averages

def create_data_table(player_dict, league_avg_dict, team_avg_dict, table_id):
    columns = [{"name": i, "id": i} for i in player_dict.keys()]
    data = [player_dict, league_avg_dict, team_avg_dict]
    return dash_table.DataTable(
        id=table_id,
        columns=columns,
        data=data,
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'paleturquoise',
            'fontWeight': 'bold'
        },
        style_data={
            'backgroundColor': 'lavender',
        }
    )

#Creates a table to display the most recent events in the game so no play is missed

def create_events_table(events):
    columns = [{"name": i, "id": i} for i in events[0].keys()] if events else []
    return dash_table.DataTable(
        id='recent-events-table',
        columns=columns,
        data=events,
        style_cell={'textAlign': 'left'},
        style_header={
            'backgroundColor': 'paleturquoise',
            'fontWeight': 'bold'
        },
        style_data={
            'backgroundColor': 'lavender',
            'minWidth': '25px',
            'width': '25px'
        },
        style_table={'height': '17.5vh', 'width': '95%', 'overflowY': 'auto', 'margin': 'auto'}
    )
