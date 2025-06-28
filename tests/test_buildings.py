import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import config as game_config # Rename to avoid conflict
from src.buildings import Building
from src.game_state import GameState # Needed for building update method context

class TestBuilding(unittest.TestCase):

    def setUp(self):
        # Create a minimal config for testing
        class MockConfig:
            SCREEN_WIDTH = 800
            SCREEN_HEIGHT = 600
            FPS = 30
            INITIAL_CREDITS = 1000
            INITIAL_POPULATION = 5
            INITIAL_POWER = 50
            RESOURCE_TYPES = ["ORE"]
            GRID_WIDTH = 10
            GRID_HEIGHT = 10
            TILE_SIZE = 16 # Crucial for get_rect()
            BUILDING_TYPES = {
                "COMMAND_CENTER": {"cost": 500, "power_draw": 10, "ui_name": "Command Base"},
                "HAB_DOME": {"cost": 100, "power_draw": 2, "capacity": 10, "ui_name": "Hab Dome"},
                "SOLAR_PANEL": {"cost": 200, "power_gen": 15, "ui_name": "Solar Panel"},
                "MINE": {"cost": 150, "power_draw": 5, "output_rate": 1, "resource_type": "ORE", "ui_name": "Mine Test"} # Changed name for clarity
            }
            FONT_FILE = "" # Not used directly by Building or GameState logic here
            CITY_RANKS = [
                {"name": "Test Rank Initial", "threshold_value": 0},
                {"name": "Test Rank Advanced", "threshold_value": 1000},
            ]
            # FPS = 30 # Already defined above, ensure it's available for GameState
            RESOURCE_NODE_TYPES = {} # Added for GameState initialization

        self.config = MockConfig()
        self.building_configs = self.config.BUILDING_TYPES # This is config_data for Building
        self.game_state = GameState(self.config)

    def test_building_creation_basic(self):
        b = Building("COMMAND_CENTER", self.building_configs, 5, 5, self.config.TILE_SIZE) # Pass TILE_SIZE
        self.assertEqual(b.type_key, "COMMAND_CENTER")
        self.assertEqual(b.ui_name, "Command Base")
        self.assertEqual(b.cost, 500)
        self.assertEqual(b.power_draw, 10)
        self.assertEqual(b.power_gen, 0)
        self.assertEqual(b.grid_x, 5)
        self.assertEqual(b.grid_y, 5)
        self.assertEqual(b.pixel_x, 5 * self.config.TILE_SIZE)
        self.assertEqual(b.pixel_y, 5 * self.config.TILE_SIZE)
        self.assertTrue(b.is_operational)

    def test_building_creation_hab_dome(self):
        b = Building("HAB_DOME", self.building_configs, 2, 3, self.config.TILE_SIZE)
        self.assertEqual(b.type_key, "HAB_DOME")
        self.assertEqual(b.capacity, 10)
        self.assertEqual(b.current_occupants, 0)

    def test_building_creation_solar_panel(self):
        b = Building("SOLAR_PANEL", self.building_configs, 1, 1, self.config.TILE_SIZE)
        self.assertEqual(b.type_key, "SOLAR_PANEL")
        self.assertEqual(b.power_gen, 15)
        self.assertEqual(b.power_draw, 0)

    def test_building_creation_mine(self):
        b = Building("MINE", self.building_configs, 4, 4, self.config.TILE_SIZE)
        self.assertEqual(b.type_key, "MINE")
        self.assertEqual(b.ui_name, "Mine Test") # Check ui_name from mock
        self.assertEqual(b.output_rate, 1)
        self.assertEqual(b.resource_type, "ORE")

    def test_get_rect(self):
        b = Building("COMMAND_CENTER", self.building_configs, 3, 3, self.config.TILE_SIZE)
        b.width_tiles = 2 # Override for testing if not in config
        b.height_tiles = 2

        expected_x = 3 * self.config.TILE_SIZE
        expected_y = 3 * self.config.TILE_SIZE
        expected_width = 2 * self.config.TILE_SIZE
        expected_height = 2 * self.config.TILE_SIZE

        rect = b.get_rect()
        self.assertEqual(rect.x, expected_x)
        self.assertEqual(rect.y, expected_y)
        self.assertEqual(rect.width, expected_width)
        self.assertEqual(rect.height, expected_height)

    def test_building_update_power_sufficient(self):
        b_consumer = Building("MINE", self.building_configs, 1, 1, self.config.TILE_SIZE) # Needs 5 power
        self.game_state.power_capacity = 100 # Plenty of power
        self.game_state.power_demand = 5 # Simulate that this demand includes the current building for the check

        b_consumer.update(self.game_state) # game_state.has_sufficient_power() will be true
        self.assertTrue(b_consumer.is_operational)

    def test_building_update_power_insufficient(self):
        b_consumer = Building("MINE", self.building_configs, 1, 1, self.config.TILE_SIZE) # Needs 5 power
        self.game_state.power_capacity = 3 # Not enough globally
        self.game_state.power_demand = 5  # Global demand is higher than capacity

        b_consumer.update(self.game_state) # game_state.has_sufficient_power() will be false
        self.assertFalse(b_consumer.is_operational)

    def test_building_update_generator(self):
        b_gen = Building("SOLAR_PANEL", self.building_configs, 0, 0, self.config.TILE_SIZE)
        # Generators should always be operational unless damaged (not implemented)
        b_gen.update(self.game_state)
        self.assertTrue(b_gen.is_operational)


if __name__ == '__main__':
    unittest.main()
