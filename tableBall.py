from dash import dash_table

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