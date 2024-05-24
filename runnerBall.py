import logging
import fetchBall
import plotly.graph_objects as go

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_and_process_game_data(game_pk):
    """
    Fetch and process game data including current play and strike zone details.
    Args:
        game_pk (int): Game package identifier.
    Returns:
        dict: Processed game data or None if an error occurs.
    """
    try:
        game_data = fetchBall.fetch_game_data(game_pk)
        if not game_data:
            logging.error("Failed to fetch game data.")
            return None

        current_play = fetchBall.fetch_current_play_data(game_data)
        strike_zone = fetchBall.fetch_strike_zone_data(game_data)

        return {'current_play': current_play, 'strike_zone': strike_zone}

    except Exception as e:
        logging.error(f"Error processing game data: {e}")
        return None

def get_base_runners(current_play):
    """
    Retrieves current base runners and their base.
    
    Args:
    current_play (dict): The game data containing current play and offense information.
    
    Returns:
    list of dicts: List containing information about each runner.
    """
    runners_info = []
    offense = current_play['scoreboard']['linescore'].get('offense', {})  # Get the offense data, default to empty dict if not found
    
    # Check for runners on each base
    for base in ['first', 'second', 'third']:
        runner = offense.get(base)  # Get the runner on the base, default to None if not found
        if runner:  # Check if runner is not None
            name = runner['fullName']
            runners_info.append({
                'name': name,
                'base': base
            })
    
    return runners_info

def get_defenders(current_play):
    """
    Retrieves current defenders and their positions.
    
    Args:
    current_play (dict): The game data containing current play and defense information.
    
    Returns:
    list of dicts: List containing information about each defender.
    """
    defenders_info = []
    defense = current_play['scoreboard']['linescore'].get('defense', {})  # Get the defense data, default to empty dict if not found
    
    # Check for defenders in each position
    for position in ['pitcher', 'catcher', 'first', 'second', 'third', 'shortstop', 'left', 'center', 'right']:
        defender = defense.get(position)  # Get the defender in the position, default to None if not found
        if defender:  # Check if defender is not None
            name = defender['fullName']
            defenders_info.append({
                'name': name,
                'position': position
            })
    
    return defenders_info