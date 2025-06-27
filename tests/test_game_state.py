import unittest
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import config as game_config # Rename to avoid conflict
from src.game_state import GameState
from src.buildings import Building

class TestGameState(unittest.TestCase):

    def setUp(self):
        # Create a minimal config for testing
        class MockConfig:
            SCREEN_WIDTH = 800
            SCREEN_HEIGHT = 600
            FPS = 30
            COLOR_BLACK = (0,0,0)
            COLOR_GREEN = (0,255,0)
            INITIAL_CREDITS = 1000
            INITIAL_POPULATION = 5
            INITIAL_POWER = 50
            RESOURCE_TYPES = ["ORE", "METAL"]
            GRID_WIDTH = 10
            GRID_HEIGHT = 10
            BUILDING_TYPES = {
                "TEST_GENERATOR": {"cost": 100, "power_gen": 20, "ui_name": "Test Gen"},
                "TEST_CONSUMER": {"cost": 50, "power_draw": 10, "ui_name": "Test Con"}
            }
            UI_FONT_SIZE = 16
            UI_PANEL_HEIGHT = 80
            UI_PADDING = 5
            GAME_VERSION = "test"
            TILE_SIZE = 16 # Needed for building rects if used, though not directly by GameState logic here
            FONT_FILE = "" # Not used by GameState directly
            # Add CITY_RANKS to MockConfig
            CITY_RANKS = [
                {"name": "Test Rank 1", "threshold_value": 0},
                {"name": "Test Rank 2", "threshold_value": 100},
            ]


        self.config = MockConfig()
        self.gs = GameState(self.config)

    def test_initial_state(self):
        self.assertEqual(self.gs.credits, self.config.INITIAL_CREDITS)
        self.assertEqual(self.gs.population, self.config.INITIAL_POPULATION)
        self.assertEqual(self.gs.power_capacity, self.config.INITIAL_POWER)
        self.assertEqual(self.gs.power_demand, 0)
        self.assertEqual(self.gs.resources["ORE"], 0)
        self.assertEqual(len(self.gs.buildings), 0)

    def test_add_building(self):
        building_data = self.config.BUILDING_TYPES
        gen_building = Building("TEST_GENERATOR", building_data, 0, 0, self.config.TILE_SIZE) # Pass TILE_SIZE

        initial_credits = self.gs.credits
        self.gs.add_building(gen_building, 0, 0)

        self.assertEqual(len(self.gs.buildings), 1)
        self.assertIn(gen_building, self.gs.buildings)
        self.assertEqual(self.gs.grid[0][0], gen_building)
        self.assertEqual(self.gs.credits, initial_credits - gen_building.cost)

        # Power balance should be updated
        self.assertEqual(self.gs.power_capacity, self.config.INITIAL_POWER + gen_building.power_gen)
        self.assertEqual(self.gs.power_demand, 0)

        con_building = Building("TEST_CONSUMER", building_data, 1, 0, self.config.TILE_SIZE) # Pass TILE_SIZE
        self.gs.add_building(con_building, 1, 0)
        self.assertEqual(len(self.gs.buildings), 2)
        self.assertEqual(self.gs.power_demand, con_building.power_draw)
        self.assertTrue(self.gs.has_sufficient_power())


    def test_remove_building(self):
        building_data = self.config.BUILDING_TYPES
        gen_building = Building("TEST_GENERATOR", building_data, 0, 0, self.config.TILE_SIZE) # Pass TILE_SIZE
        self.gs.add_building(gen_building, 0, 0)

        self.gs.remove_building(0,0)
        self.assertEqual(len(self.gs.buildings), 0)
        self.assertIsNone(self.gs.grid[0][0])
        self.assertEqual(self.gs.power_capacity, self.config.INITIAL_POWER) # Back to initial
        self.assertEqual(self.gs.power_demand, 0)


    def test_power_balance(self):
        building_data = self.config.BUILDING_TYPES
        tile_size = self.config.TILE_SIZE
        gen = Building("TEST_GENERATOR", building_data, 0, 0, tile_size) # +20 cap
        con1 = Building("TEST_CONSUMER", building_data, 0, 1, tile_size) # -10 dem
        con2 = Building("TEST_CONSUMER", building_data, 0, 2, tile_size) # -10 dem

        self.gs.add_building(gen, 0,0)
        self.gs.add_building(con1, 0,1)
        self.gs.add_building(con2, 0,2)

        self.assertEqual(self.gs.power_capacity, self.config.INITIAL_POWER + 20)
        self.assertEqual(self.gs.power_demand, 20)
        self.assertTrue(self.gs.has_sufficient_power())

        con3 = Building("TEST_CONSUMER", building_data, 0, 3, tile_size) # -10 dem (total 30)
        self.gs.add_building(con3, 0,3) # Initial 50 + Gen 20 = 70 cap. Demand 30. Still fine.
        self.assertTrue(self.gs.has_sufficient_power())

        # Add consumers to exceed capacity from generator, but not initial capacity
        con4 = Building("TEST_CONSUMER", building_data, 0, 4, tile_size) # Demand 40
        self.gs.add_building(con4,0,4)
        self.assertTrue(self.gs.has_sufficient_power())

        con5 = Building("TEST_CONSUMER", building_data, 0, 5, tile_size) # Demand 50
        self.gs.add_building(con5,0,5)
        self.assertTrue(self.gs.has_sufficient_power())

        con6 = Building("TEST_CONSUMER", building_data, 0, 6, tile_size) # Demand 60
        self.gs.add_building(con6,0,6)
        self.assertTrue(self.gs.has_sufficient_power()) # Capacity is 70, Demand is 60

        con7 = Building("TEST_CONSUMER", building_data, 0, 7, tile_size) # Demand 70
        self.gs.add_building(con7,0,7)
        self.assertTrue(self.gs.has_sufficient_power()) # Capacity is 70, Demand is 70

        con8 = Building("TEST_CONSUMER", building_data, 0, 8, tile_size) # Demand 80
        self.gs.add_building(con8,0,8)
        self.assertFalse(self.gs.has_sufficient_power()) # Capacity is 70, Demand is 80

    def test_tick(self):
        initial_time = self.gs.game_time
        self.gs.tick()
        self.assertEqual(self.gs.game_time, initial_time + 1)

if __name__ == '__main__':
    unittest.main()
