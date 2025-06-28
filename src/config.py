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
    "HAB_DOME": {"cost": 500, "power_draw": 2, "capacity": 10, "ui_name": "Habitation Dome", "unlock_conditions": {}, "income": 10}, # Always available, generates 10 credits per second
    "SOLAR_PANEL_ARRAY": {"cost": 1000, "power_gen": 20, "ui_name": "Solar Array", "unlock_conditions": {}}, # Always available
    "POWER_CONDUIT": {"cost": 50, "power_draw": 0, "ui_name": "Power Conduit", "unlock_conditions": {}}, # Always available
    "RESOURCE_EXTRACTOR": {
        "cost": 1500, "power_draw": 5, "output_rate": 1, "resource_type": "RAW_ORE",
        "ui_name": "Ore Extractor",
        "unlock_conditions": {"pop": 20} # Requires 20 population
    },
    "FACTORY_PARTS": {
        "cost": 2000, "power_draw": 15,
        "input_resource": "RAW_ORE", "input_amount": 2,
        "output_resource": "CONSTRUCTION_PARTS", "output_rate": 1, # Output 1 part
        "cycle_time_seconds": 5, # Takes 5 seconds to make 1 part
        "ui_name": "Parts Factory",
        "unlock_conditions": {"pop": 50, "tech": "basic_manufacturing"}
    },
    "LIFE_SUPPORT_NEXUS": {
        "cost": 2500, "power_draw": 20, "pop_served_bonus": 0.1,
        "ui_name": "Life Support Nexus",
        "unlock_conditions": {"rank": "Colony Supervisor"} # Requires a certain city rank
    },
    "PUMPJACK": { # Moved PUMPJACK here to keep all extractors somewhat grouped if possible, though original was fine.
        "cost": 2200, "power_draw": 15, "output_rate": 2, "resource_type": "OIL",
        "ui_name": "Oil Pumpjack", "placed_on_node_type": "OIL_NODE",
        "unlock_conditions": {"pop": 30, "rank": "Colony Starter"}
    },
    "MINER_IRON": {
        "cost": 1800, "power_draw": 10, "output_rate": 1, "resource_type": "IRON_ORE",
        "ui_name": "Iron Miner", "placed_on_node_type": "IRON_NODE",
        "unlock_conditions": {"pop": 25}
    },
    "MINER_COPPER": {
        "cost": 1800, "power_draw": 10, "output_rate": 1, "resource_type": "COPPER_ORE",
        "ui_name": "Copper Miner", "placed_on_node_type": "COPPER_NODE",
        "unlock_conditions": {"pop": 25}
    },
    "FUEL_REFINERY": {
        "cost": 3000, "power_draw": 25,
        "ui_name": "Fuel Refinery",
        "input_resource": "OIL", "input_amount": 2,
        "output_resource": "SPACESHIP_FUEL", "output_rate": 1,
        "cycle_time_seconds": 10, # Time in seconds to complete one cycle
        "unlock_conditions": {"pop": 75, "tech": "fuel_processing"}
    },
    "SPACEPORT": {
        "cost": 50000, "power_draw": 100, "ui_name": "Spaceport",
        "width_tiles": 3, "height_tiles": 3,
        "unlock_conditions": {"rank": "System Governor", "tech": "orbital_construction"} # Example high-level unlock
    }
}

SPACESHIP_PART_RECIPES = {
    "HULL_SECTION": {
        "ui_name": "Hull Section", "cost_credits": 500,
        "input_resources": {"IRON_ORE": 10, "CONSTRUCTION_PARTS": 5},
        "description": "Basic structural component for spaceships."
    },
    "ENGINE_SMALL": {
        "ui_name": "Small Thruster", "cost_credits": 1000,
        "input_resources": {"COPPER_ORE": 8, "CONSTRUCTION_PARTS": 10, "RAW_ORE": 5}, # Added RAW_ORE for complexity
        "description": "A compact thruster for small vessels."
    },
    "FUEL_TANK_SMALL": {
        "ui_name": "Small Fuel Tank", "cost_credits": 300,
        "input_resources": {"IRON_ORE": 5, "CONSTRUCTION_PARTS": 2},
        "description": "Stores a small amount of spaceship fuel."
    },
    "COCKPIT_BASIC": {
        "ui_name": "Basic Cockpit", "cost_credits": 2000,
        "input_resources": {"CONSTRUCTION_PARTS": 15, "COPPER_ORE": 5},
        "description": "Standard flight control and life support."
    },
    "CARGO_BAY_SMALL": {
        "ui_name": "Small Cargo Bay", "cost_credits": 750,
        "input_resources": {"IRON_ORE": 12, "CONSTRUCTION_PARTS": 3},
        "description": "Provides limited cargo capacity."
    }
    # TODO: Add more advanced parts (shields, weapons, larger versions etc.)
}


# Resource types
RESOURCE_TYPES = [
    "RAW_ORE", "CONSTRUCTION_PARTS", "FOOD_UNITS", # Existing
    "OIL", "IRON_ORE", "COPPER_ORE", "SPACESHIP_FUEL", "SHIP_PARTS" # New
]
# Define identifiers for resource nodes on the map resource_grid
RESOURCE_NODE_TYPES = {
    "OIL_NODE": {"color": (30,30,30), "ui_name": "Crude Oil Seep"}, # Dark grey for oil
    "IRON_NODE": {"color": (139,69,19), "ui_name": "Iron Ore Deposit"}, # Brown for iron
    "COPPER_NODE": {"color": (184,115,51), "ui_name": "Copper Ore Deposit"} # Coppery for copper
}

# Building types, technologies etc. are defined below this block in the original structure.
# I will ensure the BUILDING_TYPES dictionary is defined only once.

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
    "basic_manufacturing": {"name": "Basic Manufacturing", "cost": 5000, "unlocks_buildings": ["FACTORY_PARTS"], "description": "Enables production of construction parts."},
    "fuel_processing": {"name": "Fuel Processing", "cost": 7500, "unlocks_buildings": ["FUEL_REFINERY"], "description": "Allows refining Oil into Spaceship Fuel."},
    "orbital_construction": {"name": "Orbital Construction", "cost": 25000, "unlocks_buildings": ["SPACEPORT"], "description": "Enables construction of spaceports and large orbital structures."}
    # More techs to be added
}


# UI settings
UI_FONT_SIZE = 18
UI_TEXT_COLOR = COLOR_GREEN
UI_PANEL_HEIGHT = 100 # Height of the bottom status panel
UI_PADDING = 10

# Game version
GAME_VERSION = "0.0.1 Alpha"

# Time Control
DEFAULT_TIME_MULTIPLIER = 1
TIME_MULTIPLIER_OPTIONS = [1, 2, 5, 10] # Added 10x

print("Configuration loaded.")
