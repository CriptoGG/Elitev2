# UI elements and handling for Sci-Fi City Builder

import pygame

class Button:
    def __init__(self, x, y, width, height, text, font, text_color, button_color, hover_color, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.text_color = text_color
        self.button_color = button_color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False

    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered else self.button_color
        pygame.draw.rect(surface, current_color, self.rect)
        pygame.draw.rect(surface, self.text_color, self.rect, 1) # Border

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self):
        # Continuously update hover state based on current mouse position
        current_mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(current_mouse_pos):
            self.is_hovered = True
        else:
            self.is_hovered = False

    def handle_event(self, event):
        # MOUSEMOTION event still useful for immediate feedback if desired,
        # but update() handles the general case.
        # We can even remove the MOUSEMOTION part of handle_event if update() is called every frame before event handling.
        # For now, leave it, as it doesn't harm.
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.action:
                # Check collision directly at the moment of click
                if self.rect.collidepoint(event.pos):
                    self.is_hovered = True # Ensure hover state is true if clicked
                    self.action()
                    return True # Event handled
                else:
                    # If a click happened but not on this button, and the mouse
                    # hadn't moved away, ensure its hover state is false.
                    self.is_hovered = False
        return False


class UIPanel:
    def __init__(self, x, y, width, height, bg_color, border_color, config):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.border_color = border_color
        self.config = config
        self.elements = [] # Store text labels, buttons, etc.

        # Default font
        try:
            self.font = pygame.font.Font(config.FONT_FILE, config.UI_FONT_SIZE)
        except pygame.error: # Fallback if font file is missing
            print(f"Warning: Font file {config.FONT_FILE} not found. Using default system font.")
            self.font = pygame.font.SysFont(None, config.UI_FONT_SIZE)


    def add_text_label(self, text_func, position, color):
        """Adds a text label that can be dynamically updated via text_func."""
        self.elements.append({"type": "text", "text_func": text_func, "pos": position, "color": color})

    def add_button(self, x, y, width, height, text, action):
        # Convert panel-relative x, y to screen-absolute coordinates
        screen_x = self.rect.x + x
        screen_y = self.rect.y + y
        button = Button(screen_x, screen_y, width, height, text, self.font, self.config.UI_TEXT_COLOR, self.config.COLOR_BLUE, self.config.COLOR_AMBER, action)
        self.elements.append({"type": "button", "widget": button})
        return button


    def draw(self, surface, game_state):
        # Draw panel background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1) # Border

        # Draw elements
        for elem in self.elements:
            if elem["type"] == "text":
                text_to_render = elem["text_func"](game_state) # Get current text from function
                text_surf = self.font.render(text_to_render, True, elem["color"])
                # Position is relative to the panel's top-left corner
                surface.blit(text_surf, (self.rect.x + elem["pos"][0], self.rect.y + elem["pos"][1]))
            elif elem["type"] == "button":
                elem["widget"].update() # Update hover state
                elem["widget"].draw(surface)


    def handle_event(self, event):
        for elem in self.elements:
            if elem["type"] == "button":
                if elem["widget"].handle_event(event):
                    return True # Event handled by a button
        return False


# --- Main UI Management ---
class UIManager:
    def __init__(self, screen_width, screen_height, config):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.config = config
        self.panels = {} # e.g., {"status_panel": UIPanel(...), "build_panel": UIPanel(...)}

        self._setup_default_panels()

    def _setup_default_panels(self):
        # Status Panel (bottom)
        status_panel_height = self.config.UI_PANEL_HEIGHT
        status_panel = UIPanel(0, self.screen_height - status_panel_height,
                               self.screen_width, status_panel_height,
                               self.config.COLOR_BLACK, self.config.COLOR_GREEN, self.config)

        # Add labels to status panel (using lambdas to get current game_state values)
        # Column 1: Core Stats
        col1_x = self.config.UI_PADDING
        status_panel.add_text_label(lambda gs: f"CR: {gs.credits}", (col1_x, self.config.UI_PADDING), self.config.UI_TEXT_COLOR)
        status_panel.add_text_label(lambda gs: f"POP: {gs.population}", (col1_x, self.config.UI_PADDING + 20), self.config.UI_TEXT_COLOR)
        status_panel.add_text_label(lambda gs: f"PWR: {gs.power_demand} / {gs.power_capacity}", (col1_x, self.config.UI_PADDING + 40), self.config.UI_TEXT_COLOR)

        # Column 2: Resources
        resource_start_x = self.config.UI_PADDING + 220 # Adjusted start X for more space
        resource_y_offset = 0
        # Define which resources to display and in what order
        displayable_resources = [r for r in self.config.RESOURCE_TYPES if r not in []] # Show all for now
        # SPACESHIP_FUEL will now be shown. SHIP_PARTS also shown.

        max_res_per_col = 3 # Max resources to show in this column before starting a new one

        num_resource_cols = (len(displayable_resources) + max_res_per_col -1) // max_res_per_col
        resource_col_width = 160 # Width per resource column

        for col_idx in range(num_resource_cols):
            current_col_x = resource_start_x + (col_idx * resource_col_width)
            resource_y_offset = 0 # Reset for each new column
            for i in range(max_res_per_col):
                res_idx = col_idx * max_res_per_col + i
                if res_idx < len(displayable_resources):
                    res_type = displayable_resources[res_idx]
                    status_panel.add_text_label(
                        # Lambda needs to capture res_type correctly for each label
                        (lambda rt: lambda gs: f"{rt.replace('_', ' ').title()}: {gs.resources.get(rt, 0)}")(res_type),
                        (current_col_x, self.config.UI_PADDING + resource_y_offset),
                        self.config.UI_TEXT_COLOR
                    )
                    resource_y_offset += 20


        # Column 3 (or last column): Game Info & Actions
        # Adjust col3_x based on how many resource columns we have.
        col3_x = resource_start_x + (num_resource_cols * resource_col_width) + self.config.UI_PADDING
        # Ensure col3_x is not too far left if there are few resources. Min position:
        col3_x = max(col3_x, self.screen_width - 220)


        status_panel.add_text_label(lambda gs: f"TIME: {gs.game_time // gs.config.FPS}s", (col3_x, self.config.UI_PADDING), self.config.UI_TEXT_COLOR)
        status_panel.add_text_label(lambda gs: f"RANK: {gs.city_rank}", (col3_x, self.config.UI_PADDING + 20), self.config.UI_TEXT_COLOR)
        status_panel.add_text_label(lambda gs: f"FPS: {int(gs.clock.get_fps()) if gs.clock else 'N/A'}", (col3_x, self.config.UI_PADDING + 40), self.config.UI_TEXT_COLOR)

        # Save/Load Buttons - actions will be set in main.py
        self.save_button = status_panel.add_button(col3_x + 80, self.config.UI_PADDING, 60, 25, "SAVE", None) # Action set later
        self.load_button = status_panel.add_button(col3_x + 80, self.config.UI_PADDING + 30, 60, 25, "LOAD", None) # Action set later

        # Alerts display
        self.alert_display_duration = self.config.FPS * 3 # Display alert for 3 seconds
        self.alert_timer = 0

        status_panel.add_text_label(
            lambda gs: gs.current_alerts[0] if gs.current_alerts else "",
            (self.config.UI_PADDING, self.config.UI_PANEL_HEIGHT - self.config.UI_PADDING - self.config.UI_FONT_SIZE), # Bottom-left of panel
            self.config.COLOR_AMBER
        )


        self.panels["status_panel"] = status_panel

        # Build Panel (e.g., right side) - can be toggled
        build_panel_width = 200
        build_panel = UIPanel(self.screen_width - build_panel_width, 0,
                              build_panel_width, self.screen_height - status_panel_height,
                              self.config.COLOR_BLACK, self.config.COLOR_GREEN, self.config)
        build_panel.is_visible = True # Control visibility

        # Add build buttons (example)
        button_y = self.config.UI_PADDING
        for i, (b_key, b_data) in enumerate(self.config.BUILDING_TYPES.items()):
            # We need a way to tell the game what building to place.
            # The action here will set the game_state's selected_building_type.
            # This requires access to game_state or a callback system.
            # For now, placeholder action.
            def create_build_action(key_to_build): # Closure to capture b_key
                return lambda: print(f"Selected to build: {key_to_build}") # Placeholder

            build_panel.add_button(self.config.UI_PADDING, button_y,
                                   build_panel_width - 2 * self.config.UI_PADDING, 30,
                                   f"{b_data['ui_name']} ({b_data['cost']}CR)",
                                   create_build_action(b_key))
            button_y += 35

        self.panels["build_panel"] = build_panel


    def draw(self, surface, game_state):
        for panel_name, panel in self.panels.items():
            if hasattr(panel, 'is_visible') and not panel.is_visible:
                continue
            panel.draw(surface, game_state)

        # Handle alert display timing
        if game_state.current_alerts:
            self.alert_timer +=1
            if self.alert_timer > self.alert_display_duration:
                game_state.current_alerts.pop(0)
                self.alert_timer = 0
        else:
            self.alert_timer = 0 # Reset if no alerts


    def handle_event(self, event, game_state): # game_state is needed for button actions that might depend on it
        for panel_name, panel in self.panels.items():
            if hasattr(panel, 'is_visible') and not panel.is_visible:
                continue

            if panel.handle_event(event): # This calls the button's action if clicked
                # If a button's action was executed, it might have generated a sound implicitly
                # or one could be played here. For now, keeping sound logic mainly in main.py
                # based on the outcome of these actions.
                # Example: if a build button was clicked successfully:
                # if game_state.selected_building_type and panel_name == "build_panel":
                #    sound_manager.play_sound("ui_click") # if not handled by the action itself.
                return True # Event was handled by a button in this panel
        return False

    def set_build_panel_button_actions(self, game_state_ref):
        """Updates build panel buttons based on game_state (unlocks, affordability)."""
        build_panel = self.panels.get("build_panel")
        if build_panel:
            current_y = self.config.UI_PADDING
            build_panel.elements = [] # Clear old buttons before re-adding with new actions

            build_panel.add_text_label(lambda gs: "BUILD MENU (Rank: "+gs.city_rank+")", (self.config.UI_PADDING, current_y), self.config.UI_TEXT_COLOR)
            current_y += 25

            # --- Add Bulldozer Button ---
            def create_bulldozer_action(gs_ref):
                def action_func():
                    gs_ref.selected_building_type = None # Clear any building selection
                    gs_ref.current_tool = "bulldozer"
                    print("UI: Selected BULLDOZER tool.")
                    # TODO: Play sound_manager.play_sound("ui_click_special") or similar
                    if hasattr(gs_ref, 'sound_manager_instance') and gs_ref.sound_manager_instance: # Check if sound_manager is accessible
                        gs_ref.sound_manager_instance.play_sound("ui_click")
                return action_func

            bulldozer_action = create_bulldozer_action(game_state_ref)
            bulldozer_button_text = "BULLDOZE"
            bulldozer_color = self.config.COLOR_RED if game_state_ref.current_tool == "bulldozer" else self.config.COLOR_BLUE

            button_widget = build_panel.add_button(
                self.config.UI_PADDING, current_y,
                build_panel.rect.width - 2 * self.config.UI_PADDING, 30,
                bulldozer_button_text,
                bulldozer_action
            )
            button_widget.button_color = bulldozer_color
            button_widget.text_color = self.config.UI_TEXT_COLOR # Keep text color standard for now
            current_y += 35
            # --- End Bulldozer Button ---


            for i, (b_key, b_data) in enumerate(self.config.BUILDING_TYPES.items()):
                # Check if the building is unlocked before adding the button
                if game_state_ref.is_building_unlocked(b_key):
                    def create_build_action_with_gs(key_to_build, gs_ref):
                        # Action: set selected building type if affordable
                        def action_func():
                            gs_ref.current_tool = None # Clear bulldozer tool if active
                            # Check unlock status again just in case it changed between UI refresh and click
                            if not gs_ref.is_building_unlocked(key_to_build):
                                print(f"UI: {b_data['ui_name']} is locked.")
                                # self.sound_manager.play_sound("alert_warning") # Requires sound_manager in UIManager
                                return

                            if gs_ref.credits >= gs_ref.config.BUILDING_TYPES[key_to_build].get('cost', 0):
                                setattr(gs_ref, 'selected_building_type', key_to_build)
                                print(f"UI: Selected {key_to_build} for building.")
                                # self.sound_manager.play_sound("ui_click")
                            else:
                                print(f"UI: Cannot select {key_to_build}, not enough credits.")
                                # self.sound_manager.play_sound("insufficient_credits")
                                gs_ref.current_alerts.append(f"Need {gs_ref.config.BUILDING_TYPES[key_to_build].get('cost', 0)} CR")
                        return action_func

                    action = create_build_action_with_gs(b_key, game_state_ref)

                    button_text = f"{b_data['ui_name']} ({b_data['cost']}CR)"

                    current_button_color = self.config.COLOR_BLUE
                    text_color = self.config.UI_TEXT_COLOR

                    # Highlight if this building type is selected
                    if game_state_ref.selected_building_type == b_key:
                        current_button_color = self.config.COLOR_AMBER # Highlight selected building type

                    if game_state_ref.credits < b_data.get('cost',0):
                        current_button_color = (60,60,60) # Dim if not affordable
                        text_color = (150,150,150)


                    button_widget = build_panel.add_button(
                        self.config.UI_PADDING, current_y,
                        build_panel.rect.width - 2 * self.config.UI_PADDING, 30,
                        button_text,
                        action
                    )
                    button_widget.button_color = current_button_color
                    button_widget.text_color = text_color
                    current_y += 35
                else:
                    # Optionally, show locked buildings as greyed out / unclickable
                    button_text = f"{b_data['ui_name']} (Locked)"
                    button_widget = build_panel.add_button(
                        self.config.UI_PADDING, current_y,
                        build_panel.rect.width - 2 * self.config.UI_PADDING, 30,
                        button_text,
                        None # No action for locked buttons
                    )
                    button_widget.button_color = (30,30,30) # Very dim
                    button_widget.text_color = (100,100,100)
                    button_widget.is_hovered = False # Prevent hover effect
                    current_y += 35
                    pass


print("UI module loaded.")
