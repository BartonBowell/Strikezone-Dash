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
    Retrieves current base runners, their end base, and the event that got them on base.
    
    Args:
    current_play (dict): The game data containing current play and runners information.
    
    Returns:
    list of dicts: List containing information about each runner.
    """
    runners_info = []
    runners = current_play['scoreboard']['currentPlay'].get('runners', []) # Get the runners list, default to empty list if not found
    for runner in runners:
        if runner:  # Check if runner is not None
            name = runner['details']['runner']['fullName']
            base = runner['movement']['start']  # Directly assign the start value to base
            runners_info.append({
                'name': name,
                'base': base
            })
    return runners_info
