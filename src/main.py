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


def load_game(current_gs):
    """Loads game state from a file."""
    if not os.path.exists(SAVE_FILE_NAME):
        print(f"Save file {SAVE_FILE_NAME} not found.")
        current_gs.current_alerts.append("No save file found.")
        return

    try:
        with open(SAVE_FILE_NAME, 'r') as f:
            loaded_data = json.load(f)

        # Pass the actual buildings.Building constructor and config.BUILDING_TYPES
        if current_gs.load_from_data(loaded_data, buildings.Building, config.BUILDING_TYPES):
            print("Game loaded successfully.")
            current_gs.current_alerts.append("Game Loaded!")
            # Crucial: UI needs to be updated to reflect new state, especially build menu
            # This will be handled by the periodic ui_manager.set_build_panel_button_actions call
            # Also, explicitly refresh build panel after load as unlocks might have changed
            ui_manager.set_build_panel_button_actions(current_gs)

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
        ui_manager.load_button.action = lambda: load_game(current_game_state)

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

                        if current_game_state.selected_building_type:
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
                            elif not (0 <= grid_x < config.GRID_WIDTH and 0 <= grid_y < config.GRID_HEIGHT):
                                msg = "Out of Bounds!"
                                print(msg)
                                sound_manager_instance.play_sound("alert_warning")
                                current_game_state.current_alerts.append(msg)
                            elif current_game_state.grid[grid_y][grid_x] is not None:
                                msg = "Tile Occupied!"
                                print(msg)
                                sound_manager_instance.play_sound("alert_warning")
                                current_game_state.current_alerts.append(msg)
                            else: # All checks passed, place building
                                new_building = buildings.Building(building_key, config.BUILDING_TYPES, grid_x, grid_y, config.TILE_SIZE) # Pass TILE_SIZE
                                current_game_state.add_building(new_building, grid_x, grid_y)
                                sound_manager_instance.play_sound("building_place")
                                current_game_state.current_alerts.append(f"{new_building.ui_name} Placed.")
                        else: # No building selected, try to select an existing one or deselect all
                            clicked_b_on_grid = None
                            if 0 <= grid_x < config.GRID_WIDTH and 0 <= grid_y < config.GRID_HEIGHT:
                                clicked_b_on_grid = current_game_state.grid[grid_y][grid_x]

                            previously_selected_building = any(b.is_selected for b in current_game_state.buildings)

                            for b in current_game_state.buildings: # Deselect all first
                                b.is_selected = False

                            if clicked_b_on_grid:
                                clicked_b_on_grid.is_selected = True
                                print(f"Selected: {clicked_b_on_grid.ui_name}")
                                sound_manager_instance.play_sound("ui_click")
                            elif previously_selected_building : # Clicked empty space after something was selected
                                sound_manager_instance.play_sound("ui_click")


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_game_state.selected_building_type:
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

            # Check if buildable (basic check, more can be added)
            can_build = True
            if not (0 <= preview_grid_x < config.GRID_WIDTH and 0 <= preview_grid_y < config.GRID_HEIGHT):
                can_build = False
            elif current_game_state.grid[preview_grid_y][preview_grid_x] is not None:
                 can_build = False

            preview_color = config.COLOR_BLUE if can_build else config.COLOR_RED
            rendering.draw_wireframe_rect(screen, preview_color, preview_rect, 2)


        pygame.display.flip()
        clock.tick(config.FPS)

    print("Exiting game loop.")
    pygame.quit()

if __name__ == "__main__":
    game_loop()
