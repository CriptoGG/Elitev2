# Configuration settings for the Sci-Fi City Builder

import os

# Determine the absolute path to the project's root directory
# __file__ is the path to config.py (e.g., /path/to/project/src/config.py)
# os.path.dirname(__file__) is src directory (e.g., /path/to/project/src)
# os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) is project root (e.g., /path/to/project)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Colors (Elite-inspired: Green on Black as a base)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_AMBER = (255, 191, 0)
COLOR_RED = (255, 0, 0) # For alerts
COLOR_BLUE = (0, 0, 255) # For highlights or specific UI elements
COLOR_WHITE = (255, 255, 255) # For text or highlights

# Game settings
INITIAL_CREDITS = 10000
INITIAL_POPULATION = 10
INITIAL_POWER = 100

# File paths - now constructed from PROJECT_ROOT for robustness
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
SOUND_DIR = os.path.join(ASSETS_DIR, "sound")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
FONT_FILE = os.path.join(ASSETS_DIR, "fonts", "VectorFont.ttf") # Placeholder, will need a retro vector font

# Grid settings
TILE_SIZE = 32 # pixels
GRID_WIDTH = 50 # tiles
GRID_HEIGHT = 50 # tiles

# Building types (initial set)
# Unlock conditions: "pop": min_population, "rank": "min_rank_name", "tech": "tech_id"
BUILDING_TYPES = {
    "COMMAND_CENTER": {"cost": 5000, "power_draw": 10, "ui_name": "Command Center", "unlock_conditions": {}}, # Always available
    "HAB_DOME": {"cost": 500, "power_draw": 2, "capacity": 10, "ui_name": "Habitation Dome", "unlock_conditions": {}}, # Always available
    "SOLAR_PANEL_ARRAY": {"cost": 1000, "power_gen": 20, "ui_name": "Solar Array", "unlock_conditions": {}}, # Always available
    "POWER_CONDUIT": {"cost": 50, "power_draw": 0, "ui_name": "Power Conduit", "unlock_conditions": {}}, # Always available
    "RESOURCE_EXTRACTOR": {
        "cost": 1500, "power_draw": 5, "output_rate": 1, "resource_type": "RAW_ORE",
        "ui_name": "Ore Extractor",
        "unlock_conditions": {"pop": 20} # Requires 20 population
    },
    "FACTORY_PARTS": {
        "cost": 2000, "power_draw": 15,
        "input_resource": "RAW_ORE", "input_amount": 2, "output_resource": "CONSTRUCTION_PARTS", "output_rate": 1,
        "ui_name": "Parts Factory",
        "unlock_conditions": {"pop": 50, "tech": "basic_manufacturing"} # Requires pop and a tech
    },
    "LIFE_SUPPORT_NEXUS": {
        "cost": 2500, "power_draw": 20, "pop_served_bonus": 0.1,
        "ui_name": "Life Support Nexus",
        "unlock_conditions": {"rank": "Colony Supervisor"} # Requires a certain city rank
    }
}

# Resource types
RESOURCE_TYPES = ["RAW_ORE", "CONSTRUCTION_PARTS", "FOOD_UNITS"] # Added more for future use

# City Ranks and progression thresholds (example: total building value)
CITY_RANKS = [
    {"name": "Outpost Surveyor", "threshold_value": 0},
    {"name": "Colony Starter", "threshold_value": 10000},
    {"name": "Colony Supervisor", "threshold_value": 50000},
    {"name": "Urban Planner", "threshold_value": 150000},
    {"name": "System Governor", "threshold_value": 500000},
    {"name": "Elite Urbanist", "threshold_value": 1000000}
]

# Technologies (placeholder for now)
TECHNOLOGIES = {
    "basic_manufacturing": {"name": "Basic Manufacturing", "cost": 5000, "unlocks_buildings": ["FACTORY_PARTS"], "description": "Enables production of construction parts."}
    # More techs to be added
}


# UI settings
UI_FONT_SIZE = 18
UI_TEXT_COLOR = COLOR_GREEN
UI_PANEL_HEIGHT = 100 # Height of the bottom status panel
UI_PADDING = 10

# Game version
GAME_VERSION = "0.0.1 Alpha"

print("Configuration loaded.")
