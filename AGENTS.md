# Agent Instructions for Sci-Fi City Builder

This document provides guidance for AI agents working on this codebase.

## Project Overview

The project is a Sci-Fi City Builder game inspired by the visual aesthetic of Elite (1984). It's built using Python and Pygame. The core gameplay involves placing buildings, managing resources (credits, power, population, materials), and progressing by expanding the city and achieving higher city ranks.

## Key Modules and Their Purpose

*   **`src/main.py`**: Entry point of the game. Contains the main game loop, handles Pygame initialization, event processing (delegating to UI and game logic), and top-level rendering calls. Also includes save/load functions.
*   **`src/config.py`**: Contains all game configuration data: screen dimensions, colors, initial game settings, building type definitions (cost, power, capacity, unlock conditions), resource types, city rank progression, and (placeholder) technology definitions. **This is a crucial file for game balance and adding new content.**
*   **`src/game_state.py`**: Manages the live state of the game. This includes player resources, list of placed buildings, the city grid, game time, city rank, unlocked technologies, and current UI alerts. It also contains logic for updating game state (e.g., `tick()`, `update_power_balance()`, `update_resources_and_population()`, `check_for_rank_up()`, `is_building_unlocked()`) and methods for saving/loading game data (`get_save_data()`, `load_from_data()`).
*   **`src/buildings.py`**: Defines the `Building` class. Each building instance holds its type, configuration (from `config.py`), grid position, operational status, and specific attributes (like capacity for Hab Domes, output rate for Extractors). Includes methods for updating its state (`update()`) and drawing itself (`draw_wireframe()`).
*   **`src/rendering.py`**: Handles low-level drawing operations, such as drawing wireframe rectangles, text, and the basic UI panel structure. (Currently, building-specific wireframe details are in `buildings.py`).
*   **`src/ui.py`**: Defines UI components like `Button` and `UIPanel`. The `UIManager` class manages different UI panels (status panel, build menu), populates them with dynamic data from `GameState`, and handles UI-specific events (like button clicks).
*   **`src/sound_manager.py`**: Manages loading and playback of sound effects and background music. Includes methods to play specific sounds by name and control volume. (Actual sound files are not in the repo and need to be added by the user).
*   **`tests/`**: Contains unit tests for modules like `game_state.py` and `buildings.py`. Tests are written using Python's `unittest` module.

## Coding Conventions and Style

*   Follow PEP 8 Python style guidelines.
*   Use clear and descriptive names for variables, functions, and classes.
*   Comment complex logic or non-obvious design choices.
*   Ensure new game features or significant changes to `GameState` or `Building` logic are accompanied by corresponding unit tests.

## Common Tasks and How to Approach Them

### Adding a New Building Type

1.  **Define in `config.py`**: Add a new entry to the `BUILDING_TYPES` dictionary. Include:
    *   `cost` (integer)
    *   `power_draw` or `power_gen` (integer, positive for generation, can be 0)
    *   `ui_name` (string for display)
    *   `unlock_conditions` (dictionary, e.g., `{"pop": 50, "rank": "Colony Supervisor"}`). Empty dict `{}` means always unlocked.
    *   Any other specific attributes (e.g., `capacity` for population buildings, `resource_type` and `output_rate` for resource generators, `input_resource`/`output_resource` for factories).
2.  **Update `Building.__init__` (in `src/buildings.py`)**: If the new building has unique attributes not covered by existing `elif self.type_key == ...:` blocks, add a new block to initialize these attributes from `self.config`.
3.  **Update `Building.update()` (in `src/buildings.py`)**: If the building has active effects per tick (e.g., resource generation/consumption, unique passive effects), add logic to this method, ensuring it only runs if `self.is_operational`.
4.  **Update `Building.draw_wireframe()` (in `src/buildings.py`)**: Add a unique wireframe design for the new building. Keep it simple and in line with the Elite aesthetic.
5.  **Update `GameState.update_resources_and_population()` (in `src/game_state.py`)**: If the building affects global population capacity or has other direct impacts on game state calculations not handled in its own `update()` method, adjust here.
6.  **Testing**: Add a test case in `tests/test_buildings.py` to verify the creation and basic properties of the new building type. If it has new complex logic, consider testing that too.

### Modifying Game Balance (e.g., costs, power, progression)

*   Most balance changes will involve editing values in `src/config.py` (e.g., `BUILDING_TYPES` costs, `CITY_RANKS` thresholds).
*   Be mindful of how changes in one area can affect others (e.g., making power harder to get will impact all buildings).

### Adding New Resources

1.  Add the resource name string to `RESOURCE_TYPES` in `src/config.py`.
2.  Update `GameState.__init__` to initialize this new resource in `self.resources`.
3.  Modify the UI in `src/ui.py` (`UIManager._setup_default_panels`) to display the new resource in the status panel.
4.  Implement buildings or game mechanics that produce/consume this resource.

### Implementing New Game Mechanics

1.  **Design**: Clearly define the mechanic and how it interacts with existing systems (GameState, Buildings, UI).
2.  **Configuration**: Add any necessary configuration for the new mechanic to `src/config.py`.
3.  **GameState**: Modify `src/game_state.py` to store any new state variables and implement core logic for the mechanic.
4.  **Building Interaction**: If buildings are involved, update `src/buildings.py`.
5.  **UI**: Update `src/ui.py` to display information related to the new mechanic and provide any necessary controls.
6.  **Sound**: Add sound effects via `src/sound_manager.py` and call them from relevant points.
7.  **Testing**: Write unit tests for the new logic, especially for `GameState` changes.

## Running Tests

Ensure all tests pass after making changes:

```bash
python -m unittest tests/test_game_state.py tests/test_buildings.py
```
Or run all tests in the `tests` directory:
```bash
python -m unittest discover tests
```

## Important Considerations

*   **Elite 1984 Aesthetic**: Strive to keep visuals (wireframes, simple polygons, limited color palette) and UI minimalist, evoking the feel of the original Elite. Sound design should also be simple and retro.
*   **Performance**: While not a major concern for this style of game initially, avoid highly inefficient loops or rendering techniques, especially in `main.py`'s game loop and rendering sections.
*   **Modularity**: Continue to keep systems decoupled where possible. `config.py` should be the primary source for game data definitions.
*   **Save/Load Compatibility**: When adding new state variables to `GameState` or `Building` that need to be persisted:
    1.  Add them to `GameState.get_save_data()`.
    2.  Ensure `GameState.load_from_data()` correctly loads and initializes these new variables, providing default values if they are missing from older save files to maintain some backward compatibility if desired. Consider adding a `save_game_version` to the save file for more robust compatibility checks in the future.

By following these guidelines, AI agents can effectively contribute to the development of this Sci-Fi City Builder.Tool output for `create_file_with_block`:
