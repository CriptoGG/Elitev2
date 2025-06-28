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
                # Only update hover state for the active panel (escape menu) or if game is not paused.
                # The UIManager should pass its `escape_menu_visible` state or a general `is_game_paused` flag.
                # For now, we'll assume game_state might hold a reference to ui_manager or a pause flag.
                # A simpler way is to pass a `is_active_panel` flag to draw().
                # Let's refine this by allowing UIPanel.draw to know if it's the context for active interaction.
                # However, an even simpler fix is in UIManager.draw for now. Button.update() itself is generic.
                # The decision to call update() can be made by the UIManager or UIPanel.
                # Let's assume for now that UIManager controls this.
                # So, if a panel is told to draw while game is paused, its buttons shouldn't update hover unless it's the pause menu itself.
                # This logic is better placed in UIManager.draw or by passing a flag to UIPanel.draw

                # For the refinement: UIPanel.draw will be modified to accept `is_interactive`
                #elem["widget"].update() # Original: Update hover state always
                elem["widget"].draw(surface) # Draw is always needed


    def draw(self, surface, game_state, is_interactive_panel=True): # Added is_interactive_panel
        # Draw panel background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1) # Border

        # Draw elements
        for elem in self.elements:
            if elem["type"] == "text":
                text_to_render = elem["text_func"](game_state) # Get current text from function
                text_surf = self.font.render(text_to_render, True, elem["color"])
                surface.blit(text_surf, (self.rect.x + elem["pos"][0], self.rect.y + elem["pos"][1]))
            elif elem["type"] == "button":
                if is_interactive_panel: # Only update button if its panel is interactive
                    elem["widget"].update()
                else: # If panel is not interactive (e.g. background panel when menu is up)
                    elem["widget"].is_hovered = False # Explicitly turn off hover
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
        self.panels = {} # e.g., {"status_panel": UIPanel(...), "build_panel": UIPanel(...), "escape_menu_panel": UIPanel(...)}
        self.escape_menu_visible = False
        self.overlay_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.overlay_surface.fill((0, 0, 0, 128)) # Semi-transparent black overlay

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
        resource_start_x = self.config.UI_PADDING + 220
        resource_y_offset = 0
        displayable_resources = [r for r in self.config.RESOURCE_TYPES if r not in []]
        max_res_per_col = 3
        num_resource_cols = (len(displayable_resources) + max_res_per_col -1) // max_res_per_col
        resource_col_width = 160

        for col_idx in range(num_resource_cols):
            current_col_x = resource_start_x + (col_idx * resource_col_width)
            resource_y_offset = 0
            for i in range(max_res_per_col):
                res_idx = col_idx * max_res_per_col + i
                if res_idx < len(displayable_resources):
                    res_type = displayable_resources[res_idx]
                    status_panel.add_text_label(
                        (lambda rt: lambda gs: f"{rt.replace('_', ' ').title()}: {gs.resources.get(rt, 0)}")(res_type),
                        (current_col_x, self.config.UI_PADDING + resource_y_offset),
                        self.config.UI_TEXT_COLOR
                    )
                    resource_y_offset += 20

        # Column 3 (or last column): Game Info & Actions
        col3_x = resource_start_x + (num_resource_cols * resource_col_width) + self.config.UI_PADDING
        col3_x = max(col3_x, self.screen_width - 220)

        status_panel.add_text_label(lambda gs: f"TIME: {gs.game_time // gs.config.FPS}s ({gs.time_multiplier}x)", (col3_x, self.config.UI_PADDING), self.config.UI_TEXT_COLOR)
        status_panel.add_text_label(lambda gs: f"RANK: {gs.city_rank}", (col3_x, self.config.UI_PADDING + 20), self.config.UI_TEXT_COLOR)
        status_panel.add_text_label(lambda gs: f"FPS: {int(gs.clock.get_fps()) if gs.clock else 'N/A'}", (col3_x, self.config.UI_PADDING + 40), self.config.UI_TEXT_COLOR)

        # Time Control Buttons
        time_button_width = 30
        time_button_y = self.config.UI_PADDING + 60
        current_time_button_x = col3_x
        for i, speed in enumerate(self.config.TIME_MULTIPLIER_OPTIONS):
            status_panel.add_button(
                current_time_button_x, time_button_y, time_button_width, 25, f"{speed}x",
                None # Action set later by set_time_control_button_actions
            )
            current_time_button_x += time_button_width + 5

        # Alerts display
        self.alert_display_duration = self.config.FPS * 3
        self.alert_timer = 0
        status_panel.add_text_label(
            lambda gs: gs.current_alerts[0] if gs.current_alerts else "",
            (self.config.UI_PADDING, self.config.UI_PANEL_HEIGHT - self.config.UI_PADDING - self.config.UI_FONT_SIZE),
            self.config.COLOR_AMBER
        )
        self.panels["status_panel"] = status_panel

        # Build Panel (e.g., right side) - can be toggled
        build_panel_width = 200
        build_panel_height = self.screen_height - status_panel_height
        build_panel = UIPanel(self.screen_width - build_panel_width, 0,
                              build_panel_width, build_panel_height,
                              self.config.COLOR_BLACK, self.config.COLOR_GREEN, self.config)
        build_panel.is_visible = True
        self.panels["build_panel"] = build_panel
        # Build panel buttons are added/updated via set_build_panel_button_actions


        # --- Escape Menu Panel ---
        menu_width = 200
        menu_height = 250 # Adjusted height for more buttons
        menu_x = (self.screen_width - menu_width) // 2
        menu_y = (self.screen_height - menu_height) // 2

        escape_menu_panel = UIPanel(menu_x, menu_y, menu_width, menu_height,
                                    self.config.COLOR_GREY, self.config.COLOR_LIGHT_GREY, self.config)
        escape_menu_panel.is_visible = False # Initially hidden

        # Buttons for Escape Menu - actions will be set in main.py or by toggle_escape_menu
        button_width = menu_width - 2 * self.config.UI_PADDING
        button_height = 30
        current_menu_button_y = self.config.UI_PADDING

        escape_menu_panel.add_text_label(lambda gs: "PAUSED", (self.config.UI_PADDING, current_menu_button_y), self.config.UI_TEXT_COLOR)
        current_menu_button_y += 30

        # Resume Button - action defined here to toggle visibility
        self.resume_button = escape_menu_panel.add_button(self.config.UI_PADDING, current_menu_button_y, button_width, button_height, "Resume", self.toggle_escape_menu)
        current_menu_button_y += button_height + self.config.UI_PADDING

        # Save Button
        self.save_button = escape_menu_panel.add_button(self.config.UI_PADDING, current_menu_button_y, button_width, button_height, "Save Game", None) # Action set in main.py
        current_menu_button_y += button_height + self.config.UI_PADDING

        # Load Button
        self.load_button = escape_menu_panel.add_button(self.config.UI_PADDING, current_menu_button_y, button_width, button_height, "Load Game", None) # Action set in main.py
        current_menu_button_y += button_height + self.config.UI_PADDING

        # Quit Button
        self.quit_button = escape_menu_panel.add_button(self.config.UI_PADDING, current_menu_button_y, button_width, button_height, "Quit Game", None) # Action set in main.py

        self.panels["escape_menu_panel"] = escape_menu_panel


    def toggle_escape_menu(self):
        self.escape_menu_visible = not self.escape_menu_visible
        self.panels["escape_menu_panel"].is_visible = self.escape_menu_visible
        print(f"Escape menu toggled. Visible: {self.escape_menu_visible}")
        return self.escape_menu_visible


    def draw(self, surface, game_state):
        # Draw normal panels first
        for panel_name, panel in self.panels.items():
            if panel_name == "escape_menu_panel":
                continue
            if hasattr(panel, 'is_visible') and not panel.is_visible:
                continue
            # Pass False for is_interactive_panel if escape menu is up, otherwise True
            is_interactive = not self.escape_menu_visible
            panel.draw(surface, game_state, is_interactive_panel=is_interactive)

        # If escape menu is visible, draw overlay and then the menu (it's always interactive)
        if self.escape_menu_visible:
            surface.blit(self.overlay_surface, (0,0))
            self.panels["escape_menu_panel"].draw(surface, game_state, is_interactive_panel=True)

        # Handle alert display timing. Alerts are part of status_panel, so their interactivity is handled above.
        if game_state.current_alerts:
            self.alert_timer +=1
            if self.alert_timer > self.alert_display_duration:
                game_state.current_alerts.pop(0)
                self.alert_timer = 0
        else:
            self.alert_timer = 0 # Reset if no alerts


    def handle_event(self, event, game_state): # game_state is needed for button actions
        if self.escape_menu_visible:
            # If escape menu is active, only it should process events
            if self.panels["escape_menu_panel"].handle_event(event):
                # If the resume button (whose action is self.toggle_escape_menu) was clicked,
                # handle_event would call toggle_escape_menu, which hides the menu.
                # We need to signal to main.py that the game should unpause.
                # This could be done by the toggle_escape_menu returning a value,
                # or main.py checking the visibility status after this call.
                return True # Event handled by escape menu
            # If the event was not handled by a button in the escape menu (e.g., a click outside buttons),
            # consume it anyway to prevent interaction with underlying game/UI.
            if event.type == pygame.MOUSEBUTTONDOWN: # Consume clicks outside buttons
                 if not self.panels["escape_menu_panel"].rect.collidepoint(event.pos):
                    return True # Click was outside menu, consume it
                 else: # Click was inside menu panel but not on a button
                    # check if it was on a button, handled by panel.handle_event above
                    # if not, it's a click on the panel background, consume it.
                    is_on_button = False
                    for elem in self.panels["escape_menu_panel"].elements:
                        if elem["type"] == "button" and elem["widget"].rect.collidepoint(event.pos):
                            is_on_button = True
                            break
                    if not is_on_button:
                        return True


            return True # Consume all other events when menu is open


        # If escape menu is not visible, process events for other panels
        for panel_name, panel in self.panels.items():
            if panel_name == "escape_menu_panel": # Already handled or not visible
                continue
            if hasattr(panel, 'is_visible') and not panel.is_visible:
                continue

            if panel.handle_event(event):
                return True # Event handled by another panel
        return False

    def set_build_panel_button_actions(self, game_state_ref):
        """Updates build panel buttons based on game_state (unlocks, affordability)."""
        build_panel = self.panels.get("build_panel")
        if build_panel:
            # Optimized: Clear and re-add only if necessary or if content changes significantly.
            # For now, full refresh is simpler.
            current_y = self.config.UI_PADDING
            build_panel.elements = [] # Clear old buttons/labels

            build_panel.add_text_label(lambda gs: "BUILD MENU (Rank: "+gs.city_rank+")", (self.config.UI_PADDING, current_y), self.config.UI_TEXT_COLOR)
            current_y += 25

            # --- Add Bulldozer Button ---
            def create_bulldozer_action(gs_ref_inner): # Renamed to avoid conflict
                def action_func():
                    gs_ref_inner.selected_building_type = None
                    gs_ref_inner.current_tool = "bulldozer"
                    print("UI: Selected BULLDOZER tool.")
                    if hasattr(gs_ref_inner, 'sound_manager_instance') and gs_ref_inner.sound_manager_instance:
                        gs_ref_inner.sound_manager_instance.play_sound("ui_click")
                return action_func

            bulldozer_action = create_bulldozer_action(game_state_ref)
            bulldozer_button_text = "BULLDOZE"
            # Determine color based on current tool
            bulldozer_color = self.config.COLOR_RED if game_state_ref.current_tool == "bulldozer" else self.config.COLOR_BLUE

            button_widget = build_panel.add_button(
                self.config.UI_PADDING, current_y,
                build_panel.rect.width - 2 * self.config.UI_PADDING, 30,
                bulldozer_button_text, bulldozer_action
            )
            button_widget.button_color = bulldozer_color # Apply dynamic color
            current_y += 35
            # --- End Bulldozer Button ---

            for b_key, b_data in self.config.BUILDING_TYPES.items():
                if game_state_ref.is_building_unlocked(b_key):
                    def create_build_action_with_gs(key_to_build, gs_ref_inner):
                        def action_func():
                            gs_ref_inner.current_tool = None # Clear bulldozer
                            if not gs_ref_inner.is_building_unlocked(key_to_build):
                                print(f"UI: {b_data['ui_name']} is locked.")
                                if hasattr(gs_ref_inner, 'sound_manager_instance') and gs_ref_inner.sound_manager_instance:
                                     gs_ref_inner.sound_manager_instance.play_sound("alert_warning")
                                return
                            if gs_ref_inner.credits >= b_data.get('cost', 0):
                                gs_ref_inner.selected_building_type = key_to_build
                                print(f"UI: Selected {key_to_build} for building.")
                                if hasattr(gs_ref_inner, 'sound_manager_instance') and gs_ref_inner.sound_manager_instance:
                                     gs_ref_inner.sound_manager_instance.play_sound("ui_click")
                            else:
                                print(f"UI: Cannot select {key_to_build}, not enough credits.")
                                gs_ref_inner.current_alerts.append(f"Need {b_data['cost']} CR for {b_data['ui_name']}")
                                if hasattr(gs_ref_inner, 'sound_manager_instance') and gs_ref_inner.sound_manager_instance:
                                     gs_ref_inner.sound_manager_instance.play_sound("error_credits")
                        return action_func

                    action = create_build_action_with_gs(b_key, game_state_ref)
                    button_text = f"{b_data['ui_name']} ({b_data['cost']}CR)"
                    current_button_color = self.config.COLOR_BLUE
                    text_color = self.config.UI_TEXT_COLOR

                    if game_state_ref.selected_building_type == b_key:
                        current_button_color = self.config.COLOR_AMBER
                    if game_state_ref.credits < b_data.get('cost',0):
                        current_button_color = (60,60,60)
                        text_color = (150,150,150)

                    button_widget_instance = build_panel.add_button(
                        self.config.UI_PADDING, current_y,
                        build_panel.rect.width - 2 * self.config.UI_PADDING, 30,
                        button_text, action
                    )
                    button_widget_instance.button_color = current_button_color
                    button_widget_instance.text_color = text_color
                    current_y += 35
                else: # Locked building
                    button_text = f"{b_data['ui_name']} (Locked)"
                    locked_button_widget = build_panel.add_button(
                        self.config.UI_PADDING, current_y,
                        build_panel.rect.width - 2 * self.config.UI_PADDING, 30,
                        button_text, None # No action
                    )
                    locked_button_widget.button_color = (30,30,30)
                    locked_button_widget.text_color = (100,100,100)
                    current_y += 35

    def set_time_control_button_actions(self, game_state_ref):
        """Sets the correct game_state reference for time control button actions and updates their appearance."""
        status_panel = self.panels.get("status_panel")
        if status_panel:
        time_button_idx = 0
            for elem in status_panel.elements:
            if elem["type"] == "button" and "widget" in elem and "x" in elem["widget"].text: # Identify time buttons
                    if time_button_idx < len(self.config.TIME_MULTIPLIER_OPTIONS):
                        speed = self.config.TIME_MULTIPLIER_OPTIONS[time_button_idx]

                    def create_time_action(gs_ref_inner, multiplier_inner): # Unique names for closure
                            def action_func():
                            if self.escape_menu_visible: return # Don't change time if menu is open / game paused

                            gs_ref_inner.time_multiplier = multiplier_inner
                            print(f"UI: Time multiplier set to {multiplier_inner}x")
                            if hasattr(gs_ref_inner, 'sound_manager_instance') and gs_ref_inner.sound_manager_instance:
                                gs_ref_inner.sound_manager_instance.play_sound("ui_click")
                            self.set_time_control_button_actions(gs_ref_inner) # Refresh appearance
                            return action_func

                        elem["widget"].action = create_time_action(game_state_ref, speed)

                        if game_state_ref.time_multiplier == speed:
                        elem["widget"].button_color = self.config.COLOR_AMBER
                            elem["widget"].text_color = self.config.COLOR_BLACK
                        else:
                        elem["widget"].button_color = self.config.COLOR_BLUE
                            elem["widget"].text_color = self.config.UI_TEXT_COLOR
                        time_button_idx += 1

print("UI module loaded.")
