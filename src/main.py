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
    sound_manager_instance = sound_manager.SoundManager(config)
    ui_manager = ui.UIManager(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config)

    # --- Assign actions to Escape Menu buttons ---
    # Save Button
    if hasattr(ui_manager, 'save_button') and ui_manager.save_button:
        ui_manager.save_button.action = lambda: save_game(current_game_state)

    # Load Button
    if hasattr(ui_manager, 'load_button') and ui_manager.load_button:
        # Pass ui_manager to the load_game function via lambda for UI refresh after load
        ui_manager.load_button.action = lambda: load_game(current_game_state, ui_manager)

    # Quit Button
    # We need a way to modify 'running' from the lambda.
    # A mutable type like a list can be used, or make 'running' an attribute of a class instance.
    # For simplicity here, we'll define a helper that can change 'running'.
    # This is a bit of a hack for a local variable. A Game class would be cleaner.

    # To make 'running' modifiable by lambda, we can wrap it or use a more robust approach.
    # For now, let's assume 'running' will be handled by a direct assignment later if needed,
    # or we can make game_loop return a status.
    # The simplest for now:
    def quit_game_action():
        nonlocal running # This allows the lambda to modify the 'running' in game_loop's scope
        running = False
        print("UI: Quit button pressed. Setting running to False.")

    if hasattr(ui_manager, 'quit_button') and ui_manager.quit_button:
        ui_manager.quit_button.action = quit_game_action

    # Resume button's action is already set in ui.py to toggle the menu.
    # We will handle the game pause/unpause logic based on menu visibility.

    ui_manager.set_build_panel_button_actions(current_game_state)
    current_game_state.sound_manager_instance = sound_manager_instance
    ui_manager.set_time_control_button_actions(current_game_state)

    clock = pygame.time.Clock()
    current_game_state.clock = clock
    running = True
    game_paused = False # To control game logic updates and rendering
    previous_time_multiplier = current_game_state.time_multiplier # Store initial multiplier

    camera_offset_x = 0
    camera_offset_y = 0
    camera_speed = 10

    print("Starting game loop...")
    while running:
        mouse_pos = pygame.mouse.get_pos() # Get mouse position once per frame

        # Store previous pause state to detect changes
        was_paused = game_paused

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break # Exit event loop immediately

            # --- Escape Key for Menu Toggle ---
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # First, check if any text input is active or similar modal state, if we add those later.
                # For now, Esc always toggles the menu or clears selections.

                # If menu is NOT visible, and a tool/selection is active, clear it first.
                if not ui_manager.escape_menu_visible:
                    if current_game_state.current_tool == "bulldozer":
                        current_game_state.current_tool = None
                        sound_manager_instance.play_sound("ui_click")
                        print("Cleared bulldozer tool selection via Esc.")
                        continue # Consumed Esc for this purpose
                    elif current_game_state.selected_building_type:
                        current_game_state.selected_building_type = None
                        sound_manager_instance.play_sound("ui_click")
                        print("Cleared building selection via Esc.")
                        continue # Consumed Esc for this purpose

                # If no tool/selection was active, or if menu was already visible, toggle menu.
                ui_manager.toggle_escape_menu()
                # The pause/unpause logic is handled below based on ui_manager.escape_menu_visible
                continue # Event handled by toggling menu

            # --- UI Event Handling ---
            # The ui_manager.handle_event now also considers the escape menu state.
            # If escape menu is visible, it consumes events.
            # If resume is clicked, toggle_escape_menu is called from within button's action.
            if ui_manager.handle_event(event, current_game_state):
                # If a UI button was clicked (and it's not the resume button causing a pause state change here)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if the click was on an actual button widget within the active panel
                    clicked_on_button = False
                    active_panel_name = "escape_menu_panel" if ui_manager.escape_menu_visible else None

                    if not active_panel_name: # Check other panels if escape menu not active
                        for panel_name, panel_obj in ui_manager.panels.items():
                            if panel_name == "escape_menu_panel": continue
                            if hasattr(panel_obj, 'is_visible') and not panel_obj.is_visible: continue
                            if panel_obj.rect.collidepoint(mouse_pos):
                                active_panel_name = panel_name
                                break

                    if active_panel_name and active_panel_name in ui_manager.panels:
                        panel_to_check = ui_manager.panels[active_panel_name]
                        if panel_to_check.rect.collidepoint(mouse_pos):
                             for elem in panel_to_check.elements:
                                if elem["type"] == "button" and elem["widget"].rect.collidepoint(mouse_pos):
                                    if elem["widget"].action:
                                        clicked_on_button = True
                                        break
                    if clicked_on_button:
                        sound_manager_instance.play_sound("ui_click")
                continue # UI handled the event, or consumed it if menu was open.

            # --- Game World Interaction (only if not paused and not handled by UI) ---
            if not game_paused:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click for game world
                        on_world = True
                        # Check if click was on any visible UI panel (status bar, build menu if open)
                        for panel_key, panel_obj in ui_manager.panels.items():
                            if panel_key == "escape_menu_panel": continue # Already handled
                            if not (hasattr(panel_obj, 'is_visible') and not panel_obj.is_visible): # if visible
                                if panel_obj.rect.collidepoint(mouse_pos):
                                    on_world = False; break

                        if on_world:
                            world_x = mouse_pos[0] + camera_offset_x
                            world_y = mouse_pos[1] + camera_offset_y
                            grid_x, grid_y = world_x // config.TILE_SIZE, world_y // config.TILE_SIZE

                            if current_game_state.current_tool == "bulldozer":
                                if 0 <= grid_x < config.GRID_WIDTH and 0 <= grid_y < config.GRID_HEIGHT:
                                    building_to_remove = current_game_state.grid[grid_y][grid_x]
                                    if building_to_remove is not None:
                                        current_game_state.remove_building(grid_x, grid_y)
                                        sound_manager_instance.play_sound("alert_warning")
                                        current_game_state.current_alerts.append(f"{building_to_remove.ui_name} Demolished.")
                                    else:
                                        current_game_state.current_alerts.append("Nothing to bulldoze.")
                                    current_game_state.current_tool = None
                                else:
                                    current_game_state.current_alerts.append("Cannot bulldoze out of bounds.")
                                    current_game_state.current_tool = None
                            elif current_game_state.selected_building_type:
                                building_key = current_game_state.selected_building_type
                                building_data = config.BUILDING_TYPES[building_key]
                                building_cost = building_data.get("cost", 0)

                                if not current_game_state.is_building_unlocked(building_key):
                                    msg = f"{building_data['ui_name']} is Locked!"
                                    sound_manager_instance.play_sound("alert_warning")
                                    current_game_state.current_alerts.append(msg)
                                elif current_game_state.credits < building_cost:
                                    msg = "Insufficient Credits!"
                                    sound_manager_instance.play_sound("error_credits") # Changed sound
                                    current_game_state.current_alerts.append(msg)
                                else:
                                    can_place = True
                                    building_w = building_data.get("width_tiles", 1)
                                    building_h = building_data.get("height_tiles", 1)
                                    msg = "" # Clear previous message

                                    if not (0 <= grid_x < config.GRID_WIDTH - (building_w -1) and \
                                            0 <= grid_y < config.GRID_HEIGHT - (building_h -1)):
                                        can_place = False
                                        msg = "Out of Bounds!" # Simplified message
                                    else:
                                        for r_offset in range(building_h):
                                            for c_offset in range(building_w):
                                                if current_game_state.grid[grid_y + r_offset][grid_x + c_offset] is not None:
                                                    can_place = False; msg = "Tile Occupied!"; break
                                            if not can_place: break

                                    if not can_place:
                                        sound_manager_instance.play_sound("alert_warning")
                                        current_game_state.current_alerts.append(msg)
                                    else:
                                        new_building = buildings.Building(building_key, config.BUILDING_TYPES, grid_x, grid_y, config.TILE_SIZE)
                                        current_game_state.add_building(new_building, grid_x, grid_y)
                                        sound_manager_instance.play_sound("building_placed") # Corrected sound
                                        current_game_state.current_alerts.append(f"{new_building.ui_name} Placed.")
                                        current_game_state.selected_building_type = None
                            else: # No tool or building selected
                                current_game_state.selected_building_instance = None
                                clicked_b_on_grid = None
                                if 0 <= grid_x < config.GRID_WIDTH and 0 <= grid_y < config.GRID_HEIGHT:
                                    clicked_b_on_grid = current_game_state.grid[grid_y][grid_x]

                                previously_selected_building_on_map = any(b.is_selected for b in current_game_state.buildings if b is not None)
                                for b in current_game_state.buildings:
                                    if b: b.is_selected = False

                                if clicked_b_on_grid:
                                    clicked_b_on_grid.is_selected = True
                                    current_game_state.selected_building_instance = clicked_b_on_grid
                                    sound_manager_instance.play_sound("ui_click")
                                elif previously_selected_building_on_map :
                                    sound_manager_instance.play_sound("ui_click")
                                    current_game_state.selected_building_instance = None

                # Camera movement (only if not paused)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        camera_offset_x -= camera_speed
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        camera_offset_x += camera_speed
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        camera_offset_y -= camera_speed
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        camera_offset_y += camera_speed

                    # Clamp camera
                    # Calculate max_offset_x considering the build panel width if it's visible
                    current_build_panel_width = 0
                    if "build_panel" in ui_manager.panels and ui_manager.panels["build_panel"].is_visible:
                         current_build_panel_width = ui_manager.panels["build_panel"].rect.width

                    max_offset_x = (config.GRID_WIDTH * config.TILE_SIZE) - config.SCREEN_WIDTH + current_build_panel_width
                    max_offset_y = (config.GRID_HEIGHT * config.TILE_SIZE) - config.SCREEN_HEIGHT + config.UI_PANEL_HEIGHT # Status panel height
                    camera_offset_x = max(0, min(camera_offset_x, max_offset_x if max_offset_x > 0 else 0))
                    camera_offset_y = max(0, min(camera_offset_y, max_offset_y if max_offset_y > 0 else 0))

        if not running: break # Exit main loop if running is set to False (e.g., by quit button)

        # --- Pause State Management ---
        game_paused = ui_manager.escape_menu_visible
        if game_paused and not was_paused: # Game just paused
            previous_time_multiplier = current_game_state.time_multiplier
            current_game_state.time_multiplier = 0
            print("Game Paused. Time multiplier set to 0.")
            ui_manager.set_time_control_button_actions(current_game_state) # Refresh time buttons to show pause
        elif not game_paused and was_paused: # Game just unpaused
            current_game_state.time_multiplier = previous_time_multiplier
            print(f"Game Unpaused. Time multiplier restored to {previous_time_multiplier}.")
            ui_manager.set_time_control_button_actions(current_game_state) # Refresh time buttons


        # --- Game Logic Update (if not paused) ---
        if not game_paused:
            current_game_state.tick()
            if current_game_state.game_time % (config.FPS // 2) == 0:
                ui_manager.set_build_panel_button_actions(current_game_state)
        else: # If paused, ensure game time does not advance via tick
            # We might still want some minimal updates for UI animations if any, but GameState.tick() is the core logic.
            # For now, GameState.tick() is fully skipped.
            # We still need to update the clock for FPS display if it's part of GameState.
             if current_game_state.clock: # Ensure clock is still ticked for FPS display purposes
                current_game_state.clock.tick(config.FPS)


        # --- Rendering ---
        screen.fill(config.COLOR_BLACK)

        if not game_paused: # Only render game world if not paused
            rendering.draw_resource_nodes(screen, current_game_state, config.TILE_SIZE,
                                          camera_offset_x, camera_offset_y, config)
            building_colors = {
                "default": config.COLOR_GREEN, "selected": config.COLOR_AMBER, "inactive": (80,80,80)
            }
            for building_obj in current_game_state.buildings:
                if building_obj: building_obj.draw_wireframe(screen, building_colors, camera_offset_x, camera_offset_y)

        # Draw UI (always drawn, includes escape menu if active)
        ui_manager.draw(screen, current_game_state)

        # Preview rendering (only if not paused and a building is selected)
        if not game_paused and current_game_state.selected_building_type:
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
