import dash
from dash import Dash, html, dcc, Input, Output
from dash import dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from dash.exceptions import PreventUpdate
import pandas as pd
import pybaseball
from pybaseball import cache
import fetchBall
import tableBall
from sklearn.cluster import KMeans

cache.enable()


team_colors = {
    'ARI': '#A71930',  # Arizona Diamondbacks
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
    'MIN': '#002B5C',  # Minnesota Twins
    'NYM': '#002D72',  # New York Mets
    'NYY': '#003087',  # New York Yankees
    'OAK': '#003831',  # Oakland Athletics
    'PHI': '#E81828',  # Philadelphia Phillies
    'PIT': '#FDB827',  # Pittsburgh Pirates (added yellow color)
    'SDP': '#2F241D',  # San Diego Padres
    'SFG': '#FD5A1E',  # San Francisco Giants
    'SEA': '#0C2C56',  # Seattle Mariners
    'STL': '#C41E3A',  # St. Louis Cardinals
    'TBR': '#00285D',  # Tampa Bay Rays
    'TEX': '#003278',  # Texas Rangers
    'TOR': '#134A8E',  # Toronto Blue Jays
    'WSH': '#AB0003'   # Washington Nationals
}


app = Dash(__name__, suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP])

def purge_cache():
    cache.purge()



@app.callback(
    Output(component_id='purge-button', component_property='children'),
    [Input(component_id='purge-button', component_property='n_clicks')]
)
def update_output(n_clicks):
    if n_clicks is not None:
        purge_cache()
        return 'Cache purged'
    return 'Purge Cache'

index_page = html.Div([
    dcc.Link('Go to Player Batting Stats', href='/page-1'),
    html.Br(),
    dcc.Link('Go to Player Pitching Stats', href='/page-2'),
    html.Br(),
    dbc.Button(id='purge-button', children='Purge Cache'),
])







# Set the page layouts based on the URL path
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    year = 2021  # replace with the actual year
    end_year = 2024  # replace with the actual end year
    if pathname == '/page-1':
        df = fetchBall.fetch_stats(year, end_year, data_type='batting',qual='y')
        return tableBall.generate_layout(df)
    elif pathname == '/page-2':
        df = fetchBall.fetch_stats(year, end_year, data_type='pitching',qual='y')
        return tableBall.generate_layout(df)
    else:
        return index_page



@app.callback(
    Output('df-store', 'data'),
    [Input('year-dropdown', 'value'),
     Input('end-year-dropdown', 'value'),
     Input('data-toggle', 'value'),
     Input('ind-toggle', 'value'),
     Input('url', 'pathname'),
     Input('team-toggle', 'value')]
)
def update_df_store(year, end_year, data_toggle_value, ind, pathname, is_team_data):
    if ind == ['0']:
        ind = 0
    else:
        ind = 1
    if pathname == '/page-1':
        if data_toggle_value == 'qual':
            df = fetchBall.fetch_stats(year, end_year, data_type='batting',ind=ind,qual='y') if not is_team_data else fetchBall.fetch_combined_team_stats(year, end_year)
        else:
            df = fetchBall.fetch_stats(year, end_year, data_type='batting',ind=ind,qual=0) if not is_team_data else fetchBall.fetch_combined_team_stats(year, end_year)
    elif pathname == '/page-2':
        if data_toggle_value == 'qual':
            df = fetchBall.fetch_stats(year, end_year,  data_type='pitching',ind=ind,qual='y') if not is_team_data else pybaseball.team_pitching(year, end_year,qual='y')
        else:
            df = fetchBall.fetch_stats(year, end_year,  data_type='pitching',ind=ind,qual='y') if not is_team_data else pybaseball.team_pitching(year, end_year,qual='0')
    else:
        return dash.no_update
    return {'df': df.to_json(date_format='iso', orient='split'), 'ind': ind}


def filter_dataframe(df, qualifier_column_name, qualifier_value, comparison_operator):
    comparison_operators = {
        '<': lambda x: x < qualifier_value,
        '<=': lambda x: x <= qualifier_value,
        '=': lambda x: x == qualifier_value,
        '>': lambda x: x > qualifier_value,
        '>=': lambda x: x >= qualifier_value
    }
    return df[comparison_operators[comparison_operator](df[qualifier_column_name])]

def add_traces(fig, df, xaxis_column_name, yaxis_column_name, ind):
    grouped = df.groupby('Team')
    for team, team_data in grouped:
        if not team_data.empty:
            fig.add_trace(go.Scatter(
                x=team_data[xaxis_column_name],
                y=team_data[yaxis_column_name],
                mode='markers+text',
                text = team_data.apply(lambda row: f"{row['Name']} ({row['Season']})" if 'Name' in team_data.columns and ind == 1 else (row['Name'] if 'Name' in team_data.columns else f"{row['Team']} ({row['Season']})"), axis=1),
                textposition='top center',
                marker=dict(size=12, color=team_colors.get(team, '#999999')),  # Default color if team not in dictionary
                name=team,
                legendgroup=team,  # Grouping for toggle
                showlegend=True  # Show legend entry for each team
            ))

@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('df-store', 'data'),  # Use the data from the dcc.Store component
     Input('xaxis-column', 'value'),
     Input('yaxis-column', 'value'),
     Input('name-toggle', 'value'),
     Input('qualifier-column', 'value'),
     Input('qualifier-value', 'value'),
     Input('comparison-operator', 'value'),
     Input('invert-x-axis', 'value'),
     Input('invert-y-axis', 'value')]
)
def update_graph(stored_data, xaxis_column_name, yaxis_column_name, name_toggle_values, qualifier_column_name, qualifier_value, comparison_operator, invert_x_axis, invert_y_axis):
    df = pd.read_json(stored_data['df'], orient='split')
    ind = stored_data['ind']
    fig = go.Figure()
    cluster_colors = {0: 'red', 1: 'green', 2: 'blue'}

    #df, cluster_labels, cluster_names = create_clusters(df, [xaxis_column_name, yaxis_column_name], n_clusters=6)
    #df['Cluster'] = cluster_labels  # Add cluster labels to the dataframe

    # Apply filtering based on user inputs
    comparison_operators = {
        '<': lambda x: x < qualifier_value,
        '<=': lambda x: x <= qualifier_value,
        '=': lambda x: x == qualifier_value,
        '>': lambda x: x > qualifier_value,
        '>=': lambda x: x >= qualifier_value
    }
    df = df[comparison_operators[comparison_operator](df[qualifier_column_name])]

   
    # Group data by team and create a trace for each group
    grouped = df.groupby('Team')
    for team, team_data in grouped:
        if not team_data.empty:
            fig.add_trace(go.Scatter(
    x=team_data[xaxis_column_name],
    y=team_data[yaxis_column_name],
    mode='markers+text',
text = team_data.apply(lambda row: f"{row['Name']} ({row['Season']})" if 'Name' in team_data.columns and ind == 1 else (row['Name'] if 'Name' in team_data.columns else f"{row['Team']} ({row['Season']})"), axis=1),    textposition='top center',
    marker=dict(size=12, color=team_colors.get(team, '#999999')),  # Default color if team not in dictionary
    name=team,
    legendgroup=team,  # Grouping for toggle
    showlegend=True  # Show legend entry for each team
))

    # Calculate and display means
    mean_x = df[xaxis_column_name].mean()
    mean_y = df[yaxis_column_name].mean()
    
    # Add mean annotations
   # fig.add_annotation(
    #x=-0, y=0.90, xref='paper', yref='paper',
    #text=f'{xaxis_column_name} Mean: {mean_x:.2f}', showarrow=False, font=dict(size=14)
    #)
    #fig.add_annotation(
    #    x=-0, y=0.85, xref='paper', yref='paper',
    #    #text=f'{yaxis_column_name} Mean: {mean_y:.2f}', showarrow=False, font=dict(size=14)
    #)

    # Add quadrant labels
    x_range = df[xaxis_column_name].max() - df[xaxis_column_name].min()
    y_range = df[yaxis_column_name].max() - df[yaxis_column_name].min()

    x_offset = x_range * 0.05  # 1% of the x range
    y_offset = y_range * 0.1  # 1% of the y range

    fig.add_annotation(
        x=df[xaxis_column_name].min() + x_offset, y=df[yaxis_column_name].max() + y_offset, xref='x', yref='y',
        text=f'Low {xaxis_column_name}, High {yaxis_column_name}', showarrow=False, font=dict(size=25)
    )
    fig.add_annotation(
        x=df[xaxis_column_name].min() + x_offset, y=df[yaxis_column_name].min() - y_offset, xref='x', yref='y',
        text=f'Low {xaxis_column_name}, Low {yaxis_column_name}', showarrow=False, font=dict(size=25)
    )
    fig.add_annotation(
        x=df[xaxis_column_name].max() - x_offset, y=df[yaxis_column_name].max() + y_offset, xref='x', yref='y',
        text=f'High {xaxis_column_name}, High {yaxis_column_name}', showarrow=False, font=dict(size=25)
    )
    fig.add_annotation(
        x=df[xaxis_column_name].max() - x_offset, y=df[yaxis_column_name].min() - y_offset, xref='x', yref='y',
        text=f'High {xaxis_column_name}, Low {yaxis_column_name}', showarrow=False, font=dict(size=25)
    )

    fig.add_shape(
        go.layout.Shape(
            type="line",
            xref="paper",
            yref="y",
            x0=0,
            y0=mean_y,
            x1=1,
            y1=mean_y,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
        )
    )
    fig.add_shape(
        go.layout.Shape(
            type="line",
            xref="x",
            yref="paper",
            x0=mean_x,
            y0=0,
            x1=mean_x,
            y1=1,
            line=dict(
                color="blue",
                width=2,
                dash="dash",
            ),
        )
    )

    # Add a linear fit line if applicable
    if not df.empty and xaxis_column_name in df and yaxis_column_name in df:
        m, b = np.polyfit(df[xaxis_column_name], df[yaxis_column_name], 1)
        fig.add_trace(go.Scatter(
            x=[df[xaxis_column_name].min(), df[xaxis_column_name].max()],
            y=[m * df[xaxis_column_name].min() + b, m * df[xaxis_column_name].max() + b],
            mode='lines',
            line=dict(color='gray', width=3),
            name='Fit Line'
        ))

    # Correlation annotation
    if not df.empty and xaxis_column_name in df and yaxis_column_name in df:
        corr = np.corrcoef(df[xaxis_column_name], df[yaxis_column_name])[0, 1]
        corr_text = f'Correlation: {corr:.2f}'
        fig.add_annotation(x=-.5, y=0.80, xref='paper', yref='paper', text=corr_text, showarrow=False, font=dict(size=14))

    
    # Update layout
    fig.update_layout(
        title='Player Stats by Team',
        template='plotly_dark',
        xaxis_title=xaxis_column_name,
        yaxis_title=yaxis_column_name,
        legend_title="Teams",
        legend=dict(orientation="h", x=0, y=1.1),  # Horizontal legend outside the plot
        xaxis_autorange='reversed' if 'invert' in invert_x_axis else None,  # Invert x axis if Checklist is checked
        yaxis_autorange='reversed' if 'invert' in invert_y_axis else None  # Invert y axis if Checklist is checked
    )
    return fig




@app.callback(
    Output('yaxis-options-store', 'data'),
    [Input('df-store', 'data'),
     Input('xaxis-column', 'value')]
)
def update_yaxis_options_store(stored_data, selected_xaxis):
    df_json = stored_data['df']  # Extract 'df' from the stored data
    df = pd.read_json(df_json, orient='split')

    # Ensure only numeric columns are considered for correlation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if selected_xaxis not in numeric_cols:
        raise PreventUpdate

    # Compute correlations and sort columns by the absolute correlation value
    correlations = df[numeric_cols].corr().loc[selected_xaxis].drop(selected_xaxis, errors='ignore')
    sorted_columns = correlations.abs().sort_values(ascending=False).index.tolist()

    # Return sorted options based on correlation
    return [{'label': col, 'value': col} for col in sorted_columns]

@app.callback(
    Output('yaxis-column', 'options'),
    [Input('yaxis-options-store', 'data')]
)
def update_yaxis_options(options):
    return options


# Define the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
    dcc.Store(id='df-store'),
    dcc.Store(id='yaxis-options-store')
])



if __name__ == '__main__':
    app.run_server(debug=True,host= '0.0.0.0',port=8051)
