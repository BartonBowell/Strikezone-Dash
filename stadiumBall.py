import pandas as pd
from pathlib import Path
from functools import partial
import plotly.graph_objects as go
import runnerBall

def _transform_coordinate(coord, center, scale, sign):
    return sign * ((coord - center) * scale + center)

def transform_coordinates(coords, scale, x_center=125, y_center=199):
    x_transform = partial(_transform_coordinate, center=x_center, scale=scale, sign=+1)
    y_transform = partial(_transform_coordinate, center=y_center, scale=scale, sign=-1)
    coords['x'] = coords['x'].apply(x_transform)
    coords['y'] = coords['y'].apply(y_transform)
    return coords

# Assuming CUR_PATH is the directory where your mlbstadiums.csv file is located
CUR_PATH = Path('.')  # Modify this path as necessary
STADIUM_SCALE = 2.495 / 2.33
stadium_coords = pd.read_csv(Path(CUR_PATH, 'mlbstadiums.csv'), index_col=0)
STADIUM_COORDS = transform_coordinates(stadium_coords, scale=STADIUM_SCALE)

import plotly.graph_objects as go

def plot_stadium(team, runners=None,defenders=None, title=None, width=None, height=None):
    """
    Plot the outline of the specified team's stadium with base runners using transformed MLBAM coordinates with Plotly.
    Hovering over any point will display its x/y coordinates.
    
    Args:
        team (str): Team whose stadium will be plotted.
        runners (list of dicts): List containing dictionaries with 'name' and 'base' ('1B', '2B', '3B').
        title (str): Optional title of plot.
        width (int): Optional width of plot in browser units.
        height (int): Optional height of plot in browser units.
    
    Returns:
        Plotly graph object.
    """
    # Hardcoded base coordinates
    base_coords = {
        'first': (155, -172),  # These are example coordinates
        'second': (125, -145),
        'third': (95, -172)
    }


    position_coords = {
    #'pitcher': (125, -172),  # These are example coordinates
    'shortstop': (105, -155),
    'catcher': (125, -205),
    'first': (155, -172),
    'second': (125, -145),
    'third': (95, -172),
    
    'left': (55, -90),
    'center': (125, -70),
    'right': (180, -90)
}

    coords = STADIUM_COORDS[STADIUM_COORDS['team'] == team.lower()]
    fig = go.Figure()

    # Plot segments of the stadium
    segments = set(coords['segment'])
    for segment in segments:
        segment_verts = coords[coords['segment'] == segment]
        fig.add_trace(go.Scatter(
            x=segment_verts['x'], 
            y=segment_verts['y'], 
            fill="toself",
            mode='lines',
            line=dict(color='grey', width=2),
            hoverinfo='none'  # Disable hover info for the outline to keep it clean
        ))

    # Add base runners to the plot with hover text
    if runners:
        for runner in runners:
            base_position = runner['base']
            if base_position in base_coords:
                coord = base_coords[base_position]
                text_position = 'bottom center' if base_position in ['first', 'third'] else 'top center'
                fig.add_trace(go.Scatter(
                    x=[coord[0]],
                    y=[coord[1]],
                    mode='markers+text',
                    text=[runner['name']],
                    textposition=text_position,
                    textfont=dict(size=8),
                    marker=dict(size=10, color='blue'),
                    hovertemplate=f"Runner: {runner['name']}<br>x: %{{x}}<br>y: %{{y}}<extra></extra>"
                ))

    # Add defenders to the plot with hover text
    if defenders:
        for defender in defenders:
            position = defender['position']
            if position in position_coords:
                # Check if a runner is at the same base as the defender
                if runners and any(runner['base'] == position for runner in runners):
                    continue  # Skip this defender
                coord = position_coords[position]
                text_position = 'bottom center' if position in ['catcher', 'first', 'third','shortstop'] else 'top center'
                fig.add_trace(go.Scatter(
                    x=[coord[0]],
                    y=[coord[1]],
                    mode='markers+text',
                    text=[f"{defender['name']}"],  # Add position to label
                    textposition=text_position,
                    textfont=dict(size=8),
                    marker=dict(size=8, color='red'),
                    hovertemplate=f"Defender: {defender['name']}<br>Position: {position}<br>x: %{{x}}<br>y: %{{y}}<extra></extra>"
                ))

    # Enhance hover experience
    fig.update_layout(
        title=team if title is None else title,
        xaxis=dict(showgrid=False, zeroline=False, ticks='', showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, ticks='', showticklabels=False, scaleanchor="x", scaleratio=1),
        hovermode='closest',
        width=width,
        height=height,
        showlegend=False  # Hide the legend
    )

    return fig
