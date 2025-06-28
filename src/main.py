# Main game file for Sci-Fi City Builder

import pygame
import json # For saving and loading
import os   # For file path manipulation

from src import config
from src import rendering
from src import game_state
from src import buildings
from src import ui
from src import sound_manager # Import SoundManager

SAVE_FILE_NAME = "savegame.json"

def save_game(current_gs):
    """Saves the current game state to a file."""
    data_to_save = current_gs.get_save_data()
    try:
        with open(SAVE_FILE_NAME, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        print(f"Game saved successfully to {SAVE_FILE_NAME}")
        current_gs.current_alerts.append("Game Saved!")
    except IOError as e:
        print(f"Error saving game: {e}")
        current_gs.current_alerts.append("Error Saving Game!")


def load_game(current_gs, passed_ui_manager): # Added passed_ui_manager parameter
    """Loads game state from a file."""
    if not os.path.exists(SAVE_FILE_NAME):
        print(f"Save file {SAVE_FILE_NAME} not found.")
        current_gs.current_alerts.append("No save file found.")
        return

    try:
        with open(SAVE_FILE_NAME, 'r') as f:
            loaded_data = json.load(f)

        # Pass the actual buildings.Building constructor and config.BUILDING_TYPES
        # Also pass the ui_manager instance for UI updates after load
        if current_gs.load_from_data(loaded_data, buildings.Building, config.BUILDING_TYPES):
            print("Game loaded successfully.")
            current_gs.current_alerts.append("Game Loaded!")
            # Crucial: UI needs to be updated to reflect new state, especially build menu
            if passed_ui_manager: # Check if ui_manager was passed
                passed_ui_manager.set_build_panel_button_actions(current_gs)
            else:
                print("Warning: ui_manager not passed to load_game, UI may not refresh correctly.")


        else:
            print("Failed to load game from data.")
            current_gs.current_alerts.append("Failed to load game!")

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading game: {e}")
        current_gs.current_alerts.append("Error Loading Game!")


def game_loop():
    pygame.init()

    screen = rendering.init_display(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, f"Elite City Builder {config.GAME_VERSION}")

    # Font loading is handled within UIManager now, so this local game_font might not be needed directly in main
    # try:
    #     game_font = pygame.font.Font(config.FONT_FILE, config.UI_FONT_SIZE)
    # except pygame.error:
    #     print(f"Warning: Font file {config.FONT_FILE} not found. Using default system font.")
    #     game_font = pygame.font.SysFont(None, config.UI_FONT_SIZE)

    current_game_state = game_state.GameState(config)
    sound_manager_instance = sound_manager.SoundManager(config) # Initialize SoundManager
    ui_manager = ui.UIManager(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config) # Pass sound_manager if UI needs to play sounds directly

    # Connect Save/Load buttons
    if ui_manager.save_button: # Check if button was created
        ui_manager.save_button.action = lambda: save_game(current_game_state)
    if ui_manager.load_button:
        # Pass ui_manager to the load_game function via lambda
        ui_manager.load_button.action = lambda: load_game(current_game_state, ui_manager)

    # This ensures button actions in the UI can modify the game state (for build panel)
    ui_manager.set_build_panel_button_actions(current_game_state)


    clock = pygame.time.Clock() # For FPS control
    current_game_state.clock = clock # Give game_state access to the clock for FPS display
    running = True

    # Camera/viewport offset
    camera_offset_x = 0
    camera_offset_y = 0
    camera_speed = 10


    print("Starting game loop...")
    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Pass event to UI Manager first
            # --- Event Handling ---
            mouse_pos = pygame.mouse.get_pos() # Get mouse position once per frame for efficiency

            if ui_manager.handle_event(event, current_game_state):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if the click was on an actual button widget
                    clicked_on_button = False
                    for panel in ui_manager.panels.values():
                        if hasattr(panel, 'is_visible') and not panel.is_visible and panel_key != "build_panel": continue # Allow build panel clicks
                        if panel.rect.collidepoint(mouse_pos): # Check if click is within panel first
                            for elem in panel.elements:
                                if elem["type"] == "button" and elem["widget"].rect.collidepoint(mouse_pos):
                                    if elem["widget"].action : # Only play sound if button has an action and was truly clicked
                                        clicked_on_button = True
                                        break
                            if clicked_on_button: break
                    if clicked_on_button:
                        sound_manager_instance.play_sound("ui_click")
                continue # UI handled the event

            # Game world interaction (if not handled by UI)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    # Check if the click was on the game world (not on an active UI panel)
                    on_world = True
                    for panel_key, panel_obj in ui_manager.panels.items():
                        if panel_key == "build_panel" and not (hasattr(panel_obj, 'is_visible') and not panel_obj.is_visible):
                            # If build panel is visible, clicks on it are handled by UI
                            if panel_obj.rect.collidepoint(mouse_pos):
                                on_world = False; break
                        elif panel_key != "build_panel" and panel_obj.rect.collidepoint(mouse_pos):
                             # For other panels (like status bar), clicks on them are not world clicks
                            on_world = False; break

                    if on_world:
                        world_x = mouse_pos[0] + camera_offset_x
                        world_y = mouse_pos[1] + camera_offset_y
                        grid_x, grid_y = world_x // config.TILE_SIZE, world_y // config.TILE_SIZE

                        if current_game_state.current_tool == "bulldozer":
                            if 0 <= grid_x < config.GRID_WIDTH and 0 <= grid_y < config.GRID_HEIGHT:
                                building_to_remove = current_game_state.grid[grid_y][grid_x]
                                if building_to_remove is not None:
                                    # Optional: Add a small cost to bulldoze
                                    # bulldoze_cost = 50
                                    # if current_game_state.credits >= bulldoze_cost:
                                    #     current_game_state.credits -= bulldoze_cost
                                    #     current_game_state.remove_building(grid_x, grid_y)
                                    #     sound_manager_instance.play_sound("building_destroyed") # Need new sound
                                    #     current_game_state.current_alerts.append(f"{building_to_remove.ui_name} Demolished.")
                                    # else:
                                    #     current_game_state.current_alerts.append("Not enough credits to bulldoze.")
                                    #     sound_manager_instance.play_sound("insufficient_credits")

                                    # Simple removal for now:
                                    current_game_state.remove_building(grid_x, grid_y)
                                    sound_manager_instance.play_sound("alert_warning") # Placeholder sound, ideally a "destroyed" sound
                                    current_game_state.current_alerts.append(f"{building_to_remove.ui_name} Demolished.")
                                else:
                                    current_game_state.current_alerts.append("Nothing to bulldoze.")
                                current_game_state.current_tool = None # Deactivate bulldozer after use
                            else:
                                current_game_state.current_alerts.append("Cannot bulldoze out of bounds.")
                                current_game_state.current_tool = None # Deactivate
                        elif current_game_state.selected_building_type:
                            building_key = current_game_state.selected_building_type
                            building_data = config.BUILDING_TYPES[building_key]
                            building_cost = building_data.get("cost", 0)

                            if not current_game_state.is_building_unlocked(building_key):
                                msg = f"{building_data['ui_name']} is Locked!"
                                print(msg)
                                sound_manager_instance.play_sound("alert_warning")
                                current_game_state.current_alerts.append(msg)
                            elif current_game_state.credits < building_cost:
                                msg = "Insufficient Credits!"
                                print(msg)
                                sound_manager_instance.play_sound("insufficient_credits")
                                current_game_state.current_alerts.append(msg)

                            # Multi-tile placement check
                            else:
                                can_place = True
                                building_w = building_data.get("width_tiles", 1)
                                building_h = building_data.get("height_tiles", 1)

                                if not (0 <= grid_x < config.GRID_WIDTH - (building_w -1) and \
                                        0 <= grid_y < config.GRID_HEIGHT - (building_h -1)):
                                    can_place = False
                                    msg = "Out of Bounds (multi-tile)!"
                                else:
                                    for r_offset in range(building_h):
                                        for c_offset in range(building_w):
                                            if current_game_state.grid[grid_y + r_offset][grid_x + c_offset] is not None:
                                                can_place = False; break
                                        if not can_place: break

                                if not can_place:
                                    if msg == "": msg = "Tile Occupied (multi-tile)!" # Default if not set by bounds check
                                    print(msg)
                                    sound_manager_instance.play_sound("alert_warning")
                                    current_game_state.current_alerts.append(msg)
                                else: # All checks passed, place building
                                    new_building = buildings.Building(building_key, config.BUILDING_TYPES, grid_x, grid_y, config.TILE_SIZE)
                                    current_game_state.add_building(new_building, grid_x, grid_y) # GameState.add_building now handles multi-tile grid marking
                                    sound_manager_instance.play_sound("building_place")
                                    current_game_state.current_alerts.append(f"{new_building.ui_name} Placed.")
                                    current_game_state.selected_building_type = None # Deselect after placement

                        else: # No building selected, try to select an existing one or deselect all
                            current_game_state.selected_building_instance = None # Clear detailed selection first
                            clicked_b_on_grid = None
                            if 0 <= grid_x < config.GRID_WIDTH and 0 <= grid_y < config.GRID_HEIGHT:
                                clicked_b_on_grid = current_game_state.grid[grid_y][grid_x]

                            previously_selected_building_on_map = any(b.is_selected for b in current_game_state.buildings)

                            for b in current_game_state.buildings: # Deselect all first
                                b.is_selected = False

                            if clicked_b_on_grid:
                                clicked_b_on_grid.is_selected = True
                                current_game_state.selected_building_instance = clicked_b_on_grid # Store instance for detailed UI
                                print(f"Selected: {clicked_b_on_grid.ui_name} at ({clicked_b_on_grid.grid_x}, {clicked_b_on_grid.grid_y})")
                                sound_manager_instance.play_sound("ui_click")
                            elif previously_selected_building_on_map : # Clicked empty space after something was selected
                                sound_manager_instance.play_sound("ui_click")
                                current_game_state.selected_building_instance = None


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_game_state.current_tool == "bulldozer":
                        current_game_state.current_tool = None
                        sound_manager_instance.play_sound("ui_click")
                        print("Cleared bulldozer tool selection.")
                    elif current_game_state.selected_building_type:
                        current_game_state.selected_building_type = None # Deselect building type
                        sound_manager_instance.play_sound("ui_click")
                        print("Cleared building selection.")
                    # Potentially add more ESCAPE functionalities (e.g. close menu, pause game)
                # Camera movement
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    camera_offset_x -= camera_speed
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    camera_offset_x += camera_speed
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    camera_offset_y -= camera_speed
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    camera_offset_y += camera_speed

                # Clamp camera
                max_offset_x = (config.GRID_WIDTH * config.TILE_SIZE) - config.SCREEN_WIDTH + ui_manager.panels["build_panel"].rect.width
                max_offset_y = (config.GRID_HEIGHT * config.TILE_SIZE) - config.SCREEN_HEIGHT + config.UI_PANEL_HEIGHT
                camera_offset_x = max(0, min(camera_offset_x, max_offset_x if max_offset_x > 0 else 0))
                camera_offset_y = max(0, min(camera_offset_y, max_offset_y if max_offset_y > 0 else 0))


        # Game Logic Update
        current_game_state.tick() # Update resources, time, rank, etc.
        # Building updates are now called within game_state.tick() to ensure correct order
        # for power calculation and resource generation based on operational status.

        # Refresh build panel buttons based on current game state (unlocks, affordability)
        # This is a bit inefficient to do every frame, could be event-driven or on a timer.
        # For now, for simplicity:
        if current_game_state.game_time % (config.FPS // 2) == 0: # Update twice per second
            ui_manager.set_build_panel_button_actions(current_game_state)


        # Rendering
        screen.fill(config.COLOR_BLACK)

        # Draw Grid (optional, can be resource intensive for large grids)
        # rendering.draw_grid(screen, config.GRID_WIDTH, config.GRID_HEIGHT, config.TILE_SIZE, (30,30,30))

        # Draw Resource Nodes first, so they are under buildings
        rendering.draw_resource_nodes(screen, current_game_state, config.TILE_SIZE,
                                      camera_offset_x, camera_offset_y, config)

        # Draw Buildings (respecting camera offset)
        building_colors = {
            "default": config.COLOR_GREEN,
            "selected": config.COLOR_AMBER,
            "inactive": (80,80,80)
        }
        for building_obj in current_game_state.buildings:
            # building_obj.draw(screen, config.COLOR_GREEN, camera_offset_x, camera_offset_y)
            building_obj.draw_wireframe(screen, building_colors, camera_offset_x, camera_offset_y)

        # Draw UI (drawn on top, not affected by camera)
        ui_manager.draw(screen, current_game_state)

        # If a building type is selected for placement, draw a preview
        if current_game_state.selected_building_type:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Snap to grid for preview
            preview_grid_x = (mouse_x + camera_offset_x) // config.TILE_SIZE
            preview_grid_y = (mouse_y + camera_offset_y) // config.TILE_SIZE

            preview_pixel_x = preview_grid_x * config.TILE_SIZE - camera_offset_x
            preview_pixel_y = preview_grid_y * config.TILE_SIZE - camera_offset_y

            building_config = config.BUILDING_TYPES[current_game_state.selected_building_type]
            width_tiles = building_config.get("width_tiles", 1)
            height_tiles = building_config.get("height_tiles", 1)

            preview_rect = pygame.Rect(preview_pixel_x, preview_pixel_y, width_tiles * config.TILE_SIZE, height_tiles * config.TILE_SIZE)

            # Check if buildable (now considers multi-tile footprint)
            can_build = True
            # Check all tiles the building would occupy
            for r_offset in range(height_tiles):
                for c_offset in range(width_tiles):
                    check_x, check_y = preview_grid_x + c_offset, preview_grid_y + r_offset
                    if not (0 <= check_x < config.GRID_WIDTH and 0 <= check_y < config.GRID_HEIGHT):
                        can_build = False; break
                    if current_game_state.grid[check_y][check_x] is not None:
                        can_build = False; break
                if not can_build: break

            preview_color = config.COLOR_BLUE if can_build else config.COLOR_RED
            rendering.draw_wireframe_rect(screen, preview_color, preview_rect, 2)

        # If bulldozer tool is active, draw a special cursor/highlight
        if current_game_state.current_tool == "bulldozer":
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Check if mouse is over a panel, if so, don't draw bulldozer highlight
            on_world_for_bulldozer_preview = True
            for panel_key, panel_obj in ui_manager.panels.items():
                if panel_obj.rect.collidepoint((mouse_x, mouse_y)):
                    on_world_for_bulldozer_preview = False; break

            if on_world_for_bulldozer_preview:
                hl_grid_x = (mouse_x + camera_offset_x) // config.TILE_SIZE
                hl_grid_y = (mouse_y + camera_offset_y) // config.TILE_SIZE

                if 0 <= hl_grid_x < config.GRID_WIDTH and 0 <= hl_grid_y < config.GRID_HEIGHT:
                    hl_pixel_x = hl_grid_x * config.TILE_SIZE - camera_offset_x
                    hl_pixel_y = hl_grid_y * config.TILE_SIZE - camera_offset_y

                    highlight_rect = pygame.Rect(hl_pixel_x, hl_pixel_y, config.TILE_SIZE, config.TILE_SIZE)

                    target_building = current_game_state.grid[hl_grid_y][hl_grid_x]
                    highlight_color = config.COLOR_RED if target_building else config.COLOR_AMBER

                    rendering.draw_wireframe_rect(screen, highlight_color, highlight_rect, 3) # Thicker line for bulldozer


        pygame.display.flip()
        clock.tick(config.FPS)

    print("Exiting game loop.")
    pygame.quit()

if __name__ == "__main__":
    game_loop()
