# Defines building structures and their properties

import pygame
# from src.config import TILE_SIZE # No longer import TILE_SIZE globally

class Building:
    def __init__(self, building_type_key, config_data, grid_x, grid_y, tile_size): # Added tile_size argument
        self.type_key = building_type_key
        self.config = config_data[building_type_key] # This is the specific dict for this building type
        self.tile_size = tile_size # Store tile_size

        self.cost = self.config.get("cost", 0)
        self.power_draw = self.config.get("power_draw", 0)
        self.power_gen = self.config.get("power_gen", 0)
        self.ui_name = self.config.get("ui_name", "Building")
        self.income = self.config.get("income", 0) # Added income attribute

        self.grid_x = grid_x
        self.grid_y = grid_y

        # Dimensions in tiles (default to 1x1 if not specified)
        self.width_tiles = self.config.get("width_tiles", 1)
        self.height_tiles = self.config.get("height_tiles", 1)

        # Pixel position - uses the passed tile_size
        self.pixel_x = grid_x * self.tile_size
        self.pixel_y = grid_y * self.tile_size

        self.is_operational = True # Can be set to False due to lack of power, etc.
        self.is_selected = False

        # Specific attributes for different building types, accessed from self.config
        if self.type_key == "HAB_DOME":
            self.capacity = self.config.get("capacity", 0)
            self.current_occupants = 0
        elif self.type_key == "RESOURCE_EXTRACTOR" or self.type_key == "MINE" or \
             self.type_key == "PUMPJACK" or self.type_key == "MINER_IRON" or self.type_key == "MINER_COPPER":
            self.output_rate = self.config.get("output_rate", 0)
            self.resource_type = self.config.get("resource_type", None) # Specific extractors define this
            self.placed_on_node_type = self.config.get("placed_on_node_type", None) # What node it needs to be on
        elif self.type_key == "FUEL_REFINERY" or self.type_key == "FACTORY_PARTS": # Generalize for factory-like buildings
            self.input_resource = self.config.get("input_resource", None)
            self.input_amount = self.config.get("input_amount", 0)
            self.output_resource = self.config.get("output_resource", None)
            self.output_rate = self.config.get("output_rate", 0) # Output per cycle
            self.cycle_time_seconds = self.config.get("cycle_time_seconds", 5) # Default to 5s if not specified
            self.production_timer_ticks = 0 # Counts game ticks


        # print(f"Building '{self.ui_name}' of type '{self.type_key}' created at grid ({grid_x},{grid_y}). Using TILE_SIZE: {self.tile_size}")


    def get_rect(self):
        """Returns a pygame.Rect representing the building's footprint in pixels."""
        return pygame.Rect(self.pixel_x, self.pixel_y, self.width_tiles * self.tile_size, self.height_tiles * self.tile_size)

    def update(self, game_state):
        """Update building state each tick (e.g., production, power consumption)."""

        # Rule 1: Generators are operational unless explicitly shut down (e.g. damage - not implemented)
        if self.power_gen > 0:
            self.is_operational = True # Generators are fundamentally operational

        # Rule 2: Consumers are operational only if the grid has sufficient power *globally*
        # and they themselves are not explicitly shut down.
        elif self.power_draw > 0:
            if game_state.has_sufficient_power():
                self.is_operational = True
            else:
                # If there's not enough power globally, consumers might shut down.
                # A more complex system would have priorities. For now, all consumers go offline if global power is insufficient.
                self.is_operational = False

        # Rule 3: Buildings that neither generate nor consume significant power are always operational
        # (e.g. basic conduits, decorative structures - though Command Center does draw power)
        elif self.power_draw == 0 and self.power_gen == 0:
             self.is_operational = True


        # --- Actual resource production/consumption if operational ---
        if not self.is_operational:
            return # Don't do any work if not operational

        # Income generation (scaled by time_multiplier in GameState.tick)
        # For now, income is per second, so we check if a second has passed.
        # This will be adjusted when GameState.tick handles the multiplier.
        if self.income > 0 and game_state.game_time % game_state.config.FPS == 0: # Check once per real-time second
            # Income per second is scaled by the time multiplier.
            actual_income_this_second = self.income * game_state.time_multiplier
            game_state.credits += actual_income_this_second
            # if actual_income_this_second > 0:
                # print(f"{self.ui_name} generated {actual_income_this_second} credits (Rate: {self.income}, Multi: {game_state.time_multiplier}x). Total: {game_state.credits}")


        # Specific building logic
        if self.type_key == "HAB_DOME":
            # Population capacity is handled by game_state.update_resources_and_population
            # Hab domes themselves don't 'produce' occupants per tick here, they provide capacity.
            pass

        elif self.type_key == "SOLAR_PANEL_ARRAY":
            # Its power_gen is automatically accounted for in game_state.update_power_balance
            # if it's operational.
            pass

        elif self.type_key == "RESOURCE_EXTRACTOR" or \
             self.type_key == "PUMPJACK" or \
             self.type_key == "MINER_IRON" or \
             self.type_key == "MINER_COPPER":

            can_produce = True
            # Check if this extractor type needs to be on a specific node
            if self.placed_on_node_type:
                current_node_on_tile = game_state.resource_grid[self.grid_y][self.grid_x]
                if current_node_on_tile != self.placed_on_node_type:
                    can_produce = False

            if can_produce and self.resource_type and game_state.game_time % game_state.config.FPS == 0: # Produce once per real-time second
                if self.resource_type in game_state.resources:
                    actual_production_this_second = self.output_rate * game_state.time_multiplier
                    game_state.resources[self.resource_type] += actual_production_this_second
                    # if actual_production_this_second > 0:
                        # print(f"{self.ui_name} produced {actual_production_this_second} {self.resource_type} (Rate: {self.output_rate}, Multi: {game_state.time_multiplier}x). Total: {game_state.resources[self.resource_type]}")
                else:
                    # print(f"Warning: Resource type {self.resource_type} not in game_state.resources for {self.ui_name}")
                    pass
            # elif not can_produce and game_state.game_time % game_state.config.FPS == 0 : # Log if not producing due to wrong placement
                # print(f"{self.ui_name} at ({self.grid_x},{self.grid_y}) is not on a valid resource node ({self.placed_on_node_type} needed, found {game_state.resource_grid[self.grid_y][self.grid_x]})")

        elif self.type_key == "FUEL_REFINERY" or self.type_key == "FACTORY_PARTS": # General factory logic
            if self.input_resource and self.output_resource and self.input_amount > 0 and self.output_rate > 0:
                # Accumulate production ticks scaled by the time multiplier
                self.production_timer_ticks += (1 * game_state.time_multiplier)

                required_ticks_for_cycle = self.cycle_time_seconds * game_state.config.FPS
                # Note: required_ticks_for_cycle is in terms of 1x speed game ticks.
                # Since production_timer_ticks now accumulates faster with time_multiplier,
                # it will reach required_ticks_for_cycle sooner.

                if self.production_timer_ticks >= required_ticks_for_cycle:
                    # How many cycles have completed? (in case of very high multiplier or long frame)
                    num_cycles_completed = self.production_timer_ticks // required_ticks_for_cycle

                    for _ in range(num_cycles_completed):
                        if game_state.resources.get(self.input_resource, 0) >= self.input_amount:
                            game_state.resources[self.input_resource] -= self.input_amount
                            game_state.resources[self.output_resource] = game_state.resources.get(self.output_resource, 0) + self.output_rate
                            # print(f"{self.ui_name} consumed {self.input_amount} {self.input_resource}, produced {self.output_rate} {self.output_resource} (Cycle due to multi: {game_state.time_multiplier}x)")
                        else:
                            # Not enough input resources for a cycle, break from attempting more cycles
                            # print(f"{self.ui_name} needs {self.input_amount} of {self.input_resource} to produce. Halting further cycles this tick.")
                            break

                    # Remainder for next tick
                    self.production_timer_ticks %= required_ticks_for_cycle

                    # If we couldn't complete even one cycle due to lack of resources,
                    # and the timer was full, we should ensure it stays full to try next frame,
                    # but only if num_cycles_completed was 0.
                    if num_cycles_completed == 0 and self.production_timer_ticks >= required_ticks_for_cycle: # This check might be redundant now
                         # This case is tricky: if timer was full, but couldn't produce, it should remain full.
                         # The modulo operation might make it small.
                         # Let's re-evaluate: if production_timer_ticks >= required_ticks_for_cycle
                         # and we did 0 cycles, it means we lacked resources.
                         # The timer should ideally be "stalled" at required_ticks_for_cycle.
                        if game_state.resources.get(self.input_resource, 0) < self.input_amount:
                             self.production_timer_ticks = required_ticks_for_cycle # Stall timer
                        # print(f"{self.ui_name} needs {self.input_amount} of {self.input_resource} to produce.")
                        pass


        # Add more building-specific updates here (e.g., factories consuming input, producing output)

    def draw_wireframe(self, surface, color_map, offset_x=0, offset_y=0):
        """
        Draws the building as a wireframe.
        Color_map is a dictionary like {"default": COLOR_GREEN, "selected": COLOR_AMBER}
        Offset_x, Offset_y are for camera scrolling.
        """
        rect = self.get_rect()
        rect.x -= offset_x
        rect.y -= offset_y

        draw_color = color_map.get("selected") if self.is_selected else color_map.get("default", (0,255,0))
        if not self.is_operational and self.power_draw > 0: # Dim or color if not operational
            draw_color = color_map.get("inactive", (100,100,100))

        pygame.draw.rect(surface, draw_color, rect, 1) # Wireframe

        # Placeholder for more detailed wireframe (e.g. lines inside the rect)
        if self.type_key == "COMMAND_CENTER":
            pygame.draw.line(surface, draw_color, (rect.left, rect.top), (rect.right, rect.bottom), 1)
            pygame.draw.line(surface, draw_color, (rect.left, rect.bottom), (rect.right, rect.top), 1)
        elif self.type_key == "HAB_DOME":
            pygame.draw.circle(surface, draw_color, rect.center, min(rect.width, rect.height) // 2 - 2, 1)
        elif self.type_key == "SOLAR_PANEL_ARRAY":
            pygame.draw.line(surface, draw_color, (rect.centerx, rect.top), (rect.centerx, rect.bottom), 1)
            pygame.draw.line(surface, draw_color, (rect.left, rect.centery), (rect.right, rect.centery), 1)
        elif self.type_key == "RESOURCE_EXTRACTOR" or self.type_key == "MINER_IRON" or self.type_key == "MINER_COPPER":
            # Simple 'M' for Miner/Extractor
            pygame.draw.line(surface, draw_color, (rect.left + 2, rect.bottom - 2), (rect.left + 2, rect.top + 2), 1)
            pygame.draw.line(surface, draw_color, (rect.left + 2, rect.top + 2), (rect.centerx, rect.centery), 1)
            pygame.draw.line(surface, draw_color, (rect.centerx, rect.centery), (rect.right - 2, rect.top + 2), 1)
            pygame.draw.line(surface, draw_color, (rect.right - 2, rect.top + 2), (rect.right - 2, rect.bottom - 2), 1)
        elif self.type_key == "PUMPJACK":
            # Simple 'P' or derrick like structure
            pygame.draw.rect(surface, draw_color, rect.inflate(-rect.width * 0.6, -rect.height * 0.6), 1) # smaller inner box
            pygame.draw.line(surface, draw_color, (rect.centerx, rect.top), (rect.centerx, rect.bottom),1)
        elif self.type_key == "FACTORY_PARTS" or self.type_key == "FUEL_REFINERY":
            # Simple 'F' for Factory/Refinery
            pygame.draw.line(surface, draw_color, (rect.left + 2, rect.top + 2), (rect.left + 2, rect.bottom - 2), 1) # Vertical bar
            pygame.draw.line(surface, draw_color, (rect.left + 2, rect.top + 2), (rect.right - 2, rect.top + 2), 1) # Top bar
            pygame.draw.line(surface, draw_color, (rect.left + 2, rect.centery -2), (rect.right -5, rect.centery-2),1) # Middle bar (shorter)
        elif self.type_key == "SPACEPORT":
            # Large square with a smaller centered square or circle
            pygame.draw.rect(surface, draw_color, rect.inflate(-rect.width*0.8, -rect.height*0.8),1) # Inner small square
            # Maybe some diagonal lines to indicate a large structure
            pygame.draw.line(surface, draw_color, rect.topleft, rect.center, 1)
            pygame.draw.line(surface, draw_color, rect.topright, rect.center, 1)
            pygame.draw.line(surface, draw_color, rect.bottomleft, rect.center, 1)
            pygame.draw.line(surface, draw_color, rect.bottomright, rect.center, 1)


# Example of how to create buildings:
# building_configs = config.BUILDING_TYPES
# command_center = Building("COMMAND_CENTER", building_configs, 10, 10)
# hab_dome = Building("HAB_DOME", building_configs, 10, 12)

print("Buildings module loaded.")
