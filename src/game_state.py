# Manages the overall state of the game

# Placeholder for game state variables and logic

class GameState:
    def __init__(self, config):
        self.config = config
        self.credits = config.INITIAL_CREDITS
        self.population = config.INITIAL_POPULATION
        self.power_capacity = config.INITIAL_POWER
        self.power_demand = 0
        self.resources = {res_type: 0 for res_type in config.RESOURCE_TYPES}
        self.buildings = [] # List of placed building objects
        self.grid = [[None for _ in range(config.GRID_WIDTH)] for _ in range(config.GRID_HEIGHT)] # Represents the city grid

        self.selected_building_type = None # For construction mode
        self.current_tool = None # For tools like 'bulldozer'
        self.game_time = 0 # Could be ticks or a simulated date/time

        self.city_rank_index = 0 # Index in config.CITY_RANKS
        self.city_rank = config.CITY_RANKS[self.city_rank_index]["name"]
        self.city_value = 0 # Total cost of all buildings

        self.unlocked_technologies = set() # e.g., {"basic_manufacturing"}
        self.current_alerts = [] # List of active alerts/events
        self.clock = None # Will be set by main to get FPS

        # Resource node map
        self.resource_grid = [[None for _ in range(config.GRID_WIDTH)] for _ in range(config.GRID_HEIGHT)]
        self._generate_resource_nodes()

        self.ship_parts_inventory = {} # Stores counts of crafted ship parts, e.g. {"HULL_SECTION": 2}
        self.selected_building_instance = None # To store the actual instance of a selected building, e.g. for Spaceport UI


        print("GameState initialized.")

    def _generate_resource_nodes(self, num_patches_per_type=5, patch_size_min=2, patch_size_max=5):
        """Generates resource nodes on the map. For testing/initial setup."""
        import random
        print("Generating resource nodes...")
        for node_type_key in self.config.RESOURCE_NODE_TYPES.keys():
            for _ in range(num_patches_per_type):
                # Attempt to place a patch
                placed_patch = False
                for attempt in range(10): # Try a few times to find a spot
                    patch_width = random.randint(patch_size_min, patch_size_max)
                    patch_height = random.randint(patch_size_min, patch_size_max)
                    start_x = random.randint(0, self.config.GRID_WIDTH - patch_width)
                    start_y = random.randint(0, self.config.GRID_HEIGHT - patch_height)

                    # Check if area is clear (no other resource nodes)
                    can_place = True
                    for r in range(patch_height):
                        for c in range(patch_width):
                            if self.resource_grid[start_y + r][start_x + c] is not None:
                                can_place = False
                                break
                        if not can_place: break

                    if can_place:
                        for r in range(patch_height):
                            for c in range(patch_width):
                                # 50% chance to place node within the patch area for some sparsity
                                if random.random() < 0.7: # Make patches a bit denser
                                    self.resource_grid[start_y + r][start_x + c] = node_type_key
                        placed_patch = True
                        # print(f"Placed {node_type_key} patch at ({start_x},{start_y}) dim({patch_width}x{patch_height})")
                        break # Placed this patch, move to next patch
                # if not placed_patch:
                    # print(f"Could not place patch for {node_type_key} after {attempt+1} attempts.")
        print("Resource node generation complete.")


    def add_building(self, building_object, grid_x, grid_y):
        """Adds a building to the game state and grid."""
        # Check if building needs a specific node type (from config)
        required_node_type = building_object.config.get("placed_on_node_type")
        current_node_on_tile = self.resource_grid[grid_y][grid_x]

        if required_node_type and current_node_on_tile != required_node_type:
            # This logic is more for preventing placement, but actual production check is in Building.update()
            # For now, we allow placement but it won't work. An alert could be raised here.
            print(f"Warning: {building_object.ui_name} placed on wrong node type ({current_node_on_tile} instead of {required_node_type}). It may not function.")
            # self.current_alerts.append(f"{building_object.ui_name} needs {self.config.RESOURCE_NODE_TYPES[required_node_type]['ui_name']}")
            # return False # If we want to prevent placement entirely

        self.buildings.append(building_object)
        # Mark all tiles occupied by the building
        for r_offset in range(building_object.height_tiles):
            for c_offset in range(building_object.width_tiles):
                self.grid[grid_y + r_offset][grid_x + c_offset] = building_object

        self.credits -= building_object.cost
        self.city_value += building_object.cost
        self.update_power_balance()
        self.check_for_rank_up()
        print(f"Building {building_object.ui_name} added at ({grid_x}, {grid_y}) covering {building_object.width_tiles}x{building_object.height_tiles} tiles. Credits: {self.credits}. City Value: {self.city_value}")
        return True


    def remove_building(self, grid_x, grid_y):
        """Removes a building from the game state and grid. grid_x, grid_y is the top-left tile."""
        building_to_remove = self.grid[grid_y][grid_x]
        if building_to_remove:
            # Clear all tiles occupied by the building
            for r_offset in range(building_to_remove.height_tiles):
                for c_offset in range(building_to_remove.width_tiles):
                    # Check bounds, though ideally building data is consistent
                    if 0 <= grid_y + r_offset < self.config.GRID_HEIGHT and \
                       0 <= grid_x + c_offset < self.config.GRID_WIDTH:
                        self.grid[grid_y + r_offset][grid_x + c_offset] = None

            if building_to_remove in self.buildings:
                 self.buildings.remove(building_to_remove)
            else:
                # This might happen if remove_building is called with a non-origin tile of a multi-tile building.
                # It should ideally be called with the building_object's own grid_x, grid_y.
                # For now, we assume it's found and proceed with value/power updates.
                # A more robust solution would be to find the building instance if not at the exact x,y.
                print(f"Warning: Building at {grid_x},{grid_y} was in grid but not in master building list during removal. This may indicate an issue if it's not the top-left tile of a multi-tile building.")


            self.city_value -= building_to_remove.cost # Subtract from city value
            if self.city_value < 0: self.city_value = 0

            # Potentially refund some cost
            # self.credits += building_to_remove.cost * 0.5 # Example refund

            self.update_power_balance()
            self.check_for_rank_up() # Rank might decrease if value drops
            print(f"Building {building_to_remove.ui_name} removed from ({grid_x}, {grid_y}). City Value: {self.city_value}")
            if self.selected_building_instance == building_to_remove:
                self.selected_building_instance = None # Deselect if it was selected
        else:
            print(f"No building at ({grid_x}, {grid_y}) to remove.")


    def update_power_balance(self):
        """Recalculates total power capacity and demand based on operational buildings."""
        new_power_capacity = self.config.INITIAL_POWER # Base power
        new_power_demand = 0
        for building in self.buildings:
            if building.is_operational: # Only count operational buildings for power
                if hasattr(building, 'power_gen') and building.power_gen > 0:
                    new_power_capacity += building.power_gen
                if hasattr(building, 'power_draw') and building.power_draw > 0:
                    new_power_demand += building.power_draw
            else:
                # If a generator is not operational, it doesn't produce.
                # If a consumer is not operational, it ideally shouldn't draw power.
                # This part depends on how is_operational is set for consumers.
                # For now, we assume if it's not operational, it's not drawing.
                pass


        if new_power_capacity != self.power_capacity or new_power_demand != self.power_demand:
            self.power_capacity = new_power_capacity
            self.power_demand = new_power_demand
            # print(f"Power updated: Capacity={self.power_capacity}, Demand={self.power_demand}")

        # After updating demand and capacity, re-evaluate operational status of consumers
        # This creates a dependency: update_power_balance might call for building updates,
        # which might then call update_power_balance. This needs careful handling.
        # For now, let building.update handle its own operational status based on global power.

    def update_resources_and_population(self):
        """Updates resource generation/consumption and population based on buildings."""

        # Reset per-tick generation/consumption if necessary (or accumulate)
        # For simplicity, let's assume buildings.update() handles their own contribution
        # and game_state aggregates or directly modifies global values.

        current_population_capacity = 0
        for building in self.buildings:
            building.update(self) # Allow buildings to update their internal state / produce

            # Population Capacity
            if building.is_operational and building.type_key == "HAB_DOME":
                current_population_capacity += building.capacity

        # Simple population growth/decline based on capacity
        # More complex logic can be added (happiness, resources needed for pop, etc.)
        if self.population < current_population_capacity:
            if self.game_time % (self.config.FPS * 5) == 0: # Grow every 5 seconds approx
                self.population = min(self.population + 1, current_population_capacity)
        elif self.population > current_population_capacity:
             if self.game_time % (self.config.FPS * 2) == 0: # Decline faster if over capacity
                self.population = max(0, self.population -1)


    def has_sufficient_power(self):
        """Checks if power capacity meets or exceeds demand."""
        return self.power_capacity >= self.power_demand

    def tick(self):
        """Advances game time by one step and updates game state."""
        self.game_time += 1

        # Building updates should happen first, they might change their operational status
        for building in self.buildings:
            building.update(self) # This will set building.is_operational

        self.update_power_balance() # Recalculate power based on new operational states

        # Now that operational states and power are stable for the tick, update resources
        self.update_resources_and_population()
        self.check_for_rank_up() # Check rank regularly as pop also changes

        if self.game_time % (self.config.FPS * 1) == 0: # Log every second
             # print(f"Tick {self.game_time}. Credits: {self.credits}. Pop: {self.population}. Rank: {self.city_rank}. Power: {self.power_capacity}/{self.power_demand}. Resources: {self.resources}")
             pass

    def is_building_unlocked(self, building_key):
        """Checks if a specific building type is unlocked based on game state."""
        if building_key not in self.config.BUILDING_TYPES:
            return False # Should not happen if key is valid

        conditions = self.config.BUILDING_TYPES[building_key].get("unlock_conditions", {})
        if not conditions:
            return True # No conditions means always unlocked

        # Check population requirement
        if "pop" in conditions and self.population < conditions["pop"]:
            return False

        # Check city rank requirement
        if "rank" in conditions:
            required_rank_name = conditions["rank"]
            current_rank_index = self.city_rank_index
            required_rank_index = -1
            for i, rank_info in enumerate(self.config.CITY_RANKS):
                if rank_info["name"] == required_rank_name:
                    required_rank_index = i
                    break
            if required_rank_index == -1 or current_rank_index < required_rank_index:
                return False

        # Check technology requirement
        if "tech" in conditions and conditions["tech"] not in self.unlocked_technologies:
            return False

        return True

    def check_for_rank_up(self):
        """Checks if the city qualifies for a rank up and applies it."""
        if self.city_rank_index >= len(self.config.CITY_RANKS) - 1:
            return # Already at max rank

        next_rank_info = self.config.CITY_RANKS[self.city_rank_index + 1]

        # Progression can be based on multiple factors. For now, let's use city_value.
        # Could also include population, specific buildings constructed, etc.
        qualified_for_next_rank = False
        if self.city_value >= next_rank_info["threshold_value"]:
             # Example: also require a certain population for next rank
            # if next_rank_info.get("min_pop", 0) <= self.population:
            #    qualified_for_next_rank = True
            qualified_for_next_rank = True


        if qualified_for_next_rank:
            self.city_rank_index += 1
            old_rank = self.city_rank
            self.city_rank = self.config.CITY_RANKS[self.city_rank_index]["name"]
            print(f"CITY RANK UP! From {old_rank} to {self.city_rank}. (Value: {self.city_value})")
            # Potentially trigger an alert or UI notification
            self.current_alerts.append(f"Promoted to {self.city_rank}!")


    # More methods will be added for:
    # - Handling events (and clearing alerts)
    # - Managing trade
    # - Technology research (purchasing techs, updating self.unlocked_technologies)
    # - Calculating city metrics (happiness, efficiency, etc.)

    def get_save_data(self):
        """Collects data from game state for saving."""
        saved_buildings = []
        for building in self.buildings:
            saved_buildings.append({
                "type_key": building.type_key,
                "grid_x": building.grid_x,
                "grid_y": building.grid_y,
                # Add any other building-specific state if needed, e.g., current_occupants for HabDome
            })

        return {
            "credits": self.credits,
            "population": self.population,
            "power_capacity": self.power_capacity, # This might be recalculated on load based on buildings
            "power_demand": self.power_demand,     # Same as above
            "resources": self.resources,
            "buildings_data": saved_buildings,
            "grid_width": self.config.GRID_WIDTH, # Save for validation if grid size changes
            "grid_height": self.config.GRID_HEIGHT,
            "game_time": self.game_time,
            "city_rank_index": self.city_rank_index,
            "city_value": self.city_value,
            "unlocked_technologies": list(self.unlocked_technologies), # Convert set to list for JSON
            "game_version": self.config.GAME_VERSION # For compatibility checks
        }

    def load_from_data(self, data, building_constructor, building_configs):
        """Restores game state from loaded data."""
        try:
            # Basic validation (more can be added, e.g., version check)
            if data.get("grid_width") != self.config.GRID_WIDTH or \
               data.get("grid_height") != self.config.GRID_HEIGHT:
                print("Warning: Save file grid dimensions differ from current config. Load may be unstable.")

            self.credits = data.get("credits", self.config.INITIAL_CREDITS)
            self.population = data.get("population", self.config.INITIAL_POPULATION)
            self.resources = data.get("resources", {res_type: 0 for res_type in self.config.RESOURCE_TYPES})
            self.game_time = data.get("game_time", 0)
            self.city_rank_index = data.get("city_rank_index", 0)
            self.city_rank = self.config.CITY_RANKS[self.city_rank_index]["name"]
            self.city_value = data.get("city_value", 0)
            self.unlocked_technologies = set(data.get("unlocked_technologies", []))

            # Clear current buildings and grid
            self.buildings = []
            self.grid = [[None for _ in range(self.config.GRID_WIDTH)] for _ in range(self.config.GRID_HEIGHT)]

            # Reconstruct buildings
            loaded_buildings_data = data.get("buildings_data", [])
            for b_data in loaded_buildings_data:
                # The building_constructor is expected to be buildings.Building
                # building_configs is config.BUILDING_TYPES
                new_building = building_constructor(b_data["type_key"], building_configs, b_data["grid_x"], b_data["grid_y"])
                # Manually add to lists/grid without cost deduction or city_value update here, as that's loaded
                self.buildings.append(new_building)
                self.grid[b_data["grid_y"]][b_data["grid_x"]] = new_building
                # TODO: Restore any building-specific state if saved (e.g. occupants)

            # Crucially, recalculate power and other derived states
            self.tick() # Run a tick to ensure all states (like power, operational status) are correct
            print("Game state loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading game state: {e}")
            # Potentially reset to a default state or handle error more gracefully
            return False


print("Game State module loaded.")
