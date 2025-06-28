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
    def __init__(self, x, y, width, height, bg_color, border_color, config, element_definitions_func=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.border_color = border_color
        self.config = config
        self.elements = []  # Stores instantiated UI elements like Button objects or dicts for text
        self.element_definitions_func = element_definitions_func # Function to get element definitions

        try:
            self.font = pygame.font.Font(config.FONT_FILE, config.UI_FONT_SIZE)
            # Potentially add more font sizes here if needed for scaling
            # self.small_font = pygame.font.Font(config.FONT_FILE, config.UI_FONT_SIZE_SMALL)
        except pygame.error:
            print(f"Warning: Font file {config.FONT_FILE} not found. Using default system font.")
            self.font = pygame.font.SysFont(None, config.UI_FONT_SIZE)
            # self.small_font = pygame.font.SysFont(None, config.UI_FONT_SIZE_SMALL)

        self.is_visible = True # Default visibility

    def populate_elements(self, game_state_ref):
        """Clears and re-populates panel elements based on definitions and game_state_ref."""
        self.elements.clear()
        if self.element_definitions_func:
            element_defs = self.element_definitions_func(self.rect, game_state_ref)
            for defn in element_defs:
                if defn["type"] == "text":
                    self._add_text_from_def(defn, game_state_ref)
                elif defn["type"] == "button":
                    self._add_button_from_def(defn, game_state_ref)

    def _add_text_from_def(self, defn, game_state_ref):
        # text_func might depend on game_state_ref
        text_content = defn["text_func"](game_state_ref) if callable(defn.get("text_func")) else defn.get("text", "N/A Text")
        # pos_func depends on panel_rect (self.rect)
        position = defn["pos_func"](self.rect) if callable(defn.get("pos_func")) else defn.get("pos", (0,0))

        self.elements.append({
            "type": "text",
            "text_content": text_content, # Store rendered text or lambda to get it
            "pos": position, # Absolute position within panel
            "color": defn.get("color", self.config.UI_TEXT_COLOR),
            # "text_func": defn.get("text_func") # Keep original func if text needs re-rendering every frame
        })

    def _add_button_from_def(self, defn, game_state_ref):
        # rect_func depends on panel_rect (self.rect)
        button_rect_rel = defn["rect_func"](self.rect) if callable(defn.get("rect_func")) else pygame.Rect(0,0,100,30)
        # Button rect needs to be screen absolute for drawing and event handling
        button_rect_abs = pygame.Rect(self.rect.x + button_rect_rel.x, self.rect.y + button_rect_rel.y, button_rect_rel.width, button_rect_rel.height)

        text_content = defn["text_func"](game_state_ref) if callable(defn.get("text_func")) else defn.get("text", "Button")

        action = None
        if callable(defn.get("action_func")):
            # Action function might need game_state, so wrap it if gs_ref is available
            action_lambda = defn["action_func"]
            action = lambda: action_lambda(game_state_ref) if game_state_ref else (lambda: print("WARN: gs_ref not set for button action"))()


        button_color = self.config.COLOR_BLUE
        if callable(defn.get("color_func")):
            button_color = defn["color_func"](game_state_ref) if game_state_ref else self.config.COLOR_BLUE
        elif "color" in defn:
            button_color = defn["color"]

        text_color = self.config.UI_TEXT_COLOR
        if button_color == self.config.COLOR_AMBER : # Example: if highlighted, change text color
             text_color = self.config.COLOR_BLACK
        elif callable(defn.get("enabled_func")) and game_state_ref and not defn["enabled_func"](game_state_ref):
            button_color = (30,30,30) # Disabled color
            text_color = (100,100,100)
            action = None # Disable action

        button = Button(button_rect_abs.x, button_rect_abs.y, button_rect_abs.width, button_rect_abs.height,
                        text_content, self.font, text_color, button_color, self.config.COLOR_AMBER, action)

        # Store the widget itself
        self.elements.append({"type": "button", "widget": button, "definition": defn})


    def add_text_label(self, text_func, position, color): # Kept for now, but prefer definition based
        """DEPRECATED: Adds a text label. Use definition-based approach."""
        # This old way of adding elements is not compatible with dynamic resizing easily.
        # print("UIPanel.add_text_label is deprecated.")
        # For now, make it store things in a way that draw can still somewhat work, but without recalc.
        screen_pos = (self.rect.x + position[0], self.rect.y + position[1])
        self.elements.append({"type": "text", "text_func": text_func, "pos": screen_pos, "color": color, "_legacy": True})


    def add_button(self, x, y, width, height, text, action): # Kept for now, but prefer definition based
        """DEPRECATED: Adds a button. Use definition-based approach."""
        # print("UIPanel.add_button is deprecated.")
        screen_x = self.rect.x + x
        screen_y = self.rect.y + y
        button = Button(screen_x, screen_y, width, height, text, self.font, self.config.UI_TEXT_COLOR, self.config.COLOR_BLUE, self.config.COLOR_AMBER, action)
        self.elements.append({"type": "button", "widget": button, "_legacy": True})
        return button


    def draw(self, surface, game_state):
        if not self.is_visible:
            return

        # Draw panel background
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 1) # Border

        # Draw elements
        for elem in self.elements:
            if elem["type"] == "text":
                # If text_content is already rendered string (from _add_text_from_def)
                text_surf = self.font.render(elem["text_content"], True, elem["color"])
                # Position is already absolute to panel's origin due to pos_func(self.rect)
                surface.blit(text_surf, (self.rect.x + elem["pos"][0], self.rect.y + elem["pos"][1]))
            elif elem["type"] == "button" and elem.get("widget"):
                # Update button's hover state (its rect is screen absolute)
                elem["widget"].update()
                elem["widget"].draw(surface)


    def handle_event(self, event):
        if not self.is_visible:
            return False

        for elem in self.elements:
            if elem["type"] == "button" and elem.get("widget"):
                if elem["widget"].handle_event(event):
                    return True # Event handled by a button
        return False


# --- Main UI Management ---
class UIManager:
    def __init__(self, initial_screen_width, initial_screen_height, config):
        self.screen_width = initial_screen_width
        self.screen_height = initial_screen_height
        self.config = config
        self.panels = {} # e.g., {"status_panel": UIPanel(...), "build_panel": UIPanel(...)}
        self.game_state_ref = None # Will be set later, useful for panel recalculations
        self.save_game_func = None # To be set by main
        self.load_game_func = None # To be set by main
        self.alert_timer = 0 # Moved from _setup_default_panels to UIManager instance


        # Panel definitions will store relative layout info rather than fixed pixel values directly
        self._define_panel_layouts() # Defines panel structures and their relative positioning
        self._create_panels_from_layout() # Actually instantiates UIPanel objects

    def _define_panel_layouts(self):
        """Defines the structure and relative positioning rules for UI panels."""
        self.panel_layouts = {
            "status_panel": {
                "rect_func": lambda w, h: pygame.Rect(0, h - self.config.UI_PANEL_HEIGHT, w, self.config.UI_PANEL_HEIGHT),
                "bg_color": self.config.COLOR_BLACK,
                "border_color": self.config.COLOR_GREEN,
                "elements_func": self._define_status_panel_elements
            },
            "build_panel": {
                "rect_func": lambda w, h: pygame.Rect(w - 200, 0, 200, h - self.config.UI_PANEL_HEIGHT),
                "bg_color": self.config.COLOR_BLACK,
                "border_color": self.config.COLOR_GREEN,
                "elements_func": self._define_build_panel_elements,
                "is_visible": True
            }
            # Add other panels here if needed
        }

    def _create_panels_from_layout(self):
        """Creates UIPanel instances based on their layout definitions and current screen size."""
        self.panels.clear()
        for panel_key, layout in self.panel_layouts.items():
            rect = layout["rect_func"](self.screen_width, self.screen_height)
            panel = UIPanel(rect.x, rect.y, rect.width, rect.height,
                            layout["bg_color"], layout["border_color"], self.config,
                            element_definitions_func=layout["elements_func"]) # Pass the function
            if "is_visible" in layout:
                panel.is_visible = layout["is_visible"]

            # Populate elements using the elements_func, which now needs panel context
            panel.populate_elements(self.game_state_ref) # game_state_ref might be None initially
                                                        # Handled by button/label adders in UIPanel
            self.panels[panel_key] = panel


    def _define_status_panel_elements(self, panel_rect, gs_ref):
        """Returns a list of element definitions for the status panel."""
        elements = []
        padding = self.config.UI_PADDING
        font_size = self.config.UI_FONT_SIZE
        line_height = font_size + 4 # approx

        # Column 1: Core Stats
        col1_x = padding
        elements.append({
            "type": "text", "text_func": lambda gs: f"CR: {gs.credits if gs else 'N/A'}",
            "pos_func": lambda p_rect: (col1_x, padding), "color": self.config.UI_TEXT_COLOR
        })
        elements.append({
            "type": "text", "text_func": lambda gs: f"POP: {gs.population if gs else 'N/A'}",
            "pos_func": lambda p_rect: (col1_x, padding + line_height), "color": self.config.UI_TEXT_COLOR
        })
        elements.append({
            "type": "text", "text_func": lambda gs: f"PWR: {gs.power_demand if gs else 'N/A'} / {gs.power_capacity if gs else 'N/A'}",
            "pos_func": lambda p_rect: (col1_x, padding + 2 * line_height), "color": self.config.UI_TEXT_COLOR
        })

        # Column 2: Resources (simplified for now, needs more robust relative placement)
        # This part will require careful planning for true responsiveness.
        # For now, let's assume a fixed width area or fewer resources displayed if space is tight.
        resource_start_x = padding + 180 # Example fixed offset, needs to be relative
        current_res_y = padding
        displayable_resources = [r for r in self.config.RESOURCE_TYPES if r not in []]
        for i, res_type in enumerate(displayable_resources[:3]): # Limit for simplicity
            # Lambda needs to capture res_type correctly
            capture_res_type = res_type
            elements.append({
                "type": "text", "text_func": (lambda rt: lambda gs: f"{rt.replace('_', ' ').title()}: {gs.resources.get(rt, 0) if gs else 'N/A'}")(capture_res_type),
                "pos_func": (lambda y_offset: lambda p_rect: (resource_start_x, y_offset))(current_res_y),
                "color": self.config.UI_TEXT_COLOR
            })
            current_res_y += line_height

        # Column 3: Game Info & Actions (also needs robust relative placement)
        # Example: position from right edge of the panel
        col3_base_x_offset = 220 # Offset from the right

        elements.append({
            "type": "text", "text_func": lambda gs: f"TIME: {gs.game_time // self.config.FPS if gs else 'N/A'}s ({gs.time_multiplier if gs else 1}x)",
            "pos_func": lambda p_rect: (p_rect.width - col3_base_x_offset, padding), "color": self.config.UI_TEXT_COLOR
        })
        elements.append({
            "type": "text", "text_func": lambda gs: f"RANK: {gs.city_rank if gs else 'N/A'}",
            "pos_func": lambda p_rect: (p_rect.width - col3_base_x_offset, padding + line_height), "color": self.config.UI_TEXT_COLOR
        })
        elements.append({
            "type": "text", "text_func": lambda gs: f"FPS: {int(gs.clock.get_fps()) if gs and gs.clock else 'N/A'}",
            "pos_func": lambda p_rect: (p_rect.width - col3_base_x_offset, padding + 2 * line_height), "color": self.config.UI_TEXT_COLOR
        })

        # Time Control Buttons - position relative to col3 text
        time_button_y_base = padding + 3 * line_height
        time_button_width = 30
        time_button_height = 25
        time_button_spacing = 5

        for i, speed in enumerate(self.config.TIME_MULTIPLIER_OPTIONS):
            # Lambda to capture speed for action and text
            captured_speed = speed
            elements.append({
                "type": "button", "text": f"{captured_speed}x",
                "rect_func": (lambda idx: lambda p_rect: pygame.Rect(
                    p_rect.width - col3_base_x_offset + (idx * (time_button_width + time_button_spacing)),
                    time_button_y_base, time_button_width, time_button_height))(i),
                "action_func": (lambda sp: lambda gs: self._set_time_multiplier(gs, sp))(captured_speed)
            })

        # Save/Load Buttons - position relative to right edge, below time controls
        sl_button_y = time_button_y_base + time_button_height + padding
        sl_button_width = 60
        sl_button_x_offset = 150 # from right edge

        # Save Button
        elements.append({
            "type": "button", "text": "SAVE",
            "rect_func": lambda p_rect: pygame.Rect(p_rect.width - sl_button_x_offset, sl_button_y, sl_button_width, time_button_height),
            "action_func": lambda gs: self._save_game_action(gs) # gs is game_state_ref
        })
        # Load Button
        elements.append({
            "type": "button", "text": "LOAD",
            "rect_func": lambda p_rect: pygame.Rect(p_rect.width - sl_button_x_offset + sl_button_width + padding, sl_button_y, sl_button_width, time_button_height),
            "action_func": lambda gs: self._load_game_action(gs) # gs is game_state_ref
        })

        # Alerts (bottom-left of panel)
        elements.append({
            "type": "text", "text_func": lambda gs: gs.current_alerts[0] if gs and gs.current_alerts else "",
            "pos_func": lambda p_rect: (padding, p_rect.height - padding - font_size),
            "color": self.config.COLOR_AMBER
        })
        return elements

    def _define_build_panel_elements(self, panel_rect, gs_ref):
        """Returns a list of element definitions for the build panel."""
        elements = []
        padding = self.config.UI_PADDING
        button_height = 30
        button_spacing = 5
        current_y = padding

        elements.append({
            "type": "text", "text_func": lambda gs: f"BUILD (Rank: {gs.city_rank if gs else 'N/A'})",
            "pos_func": lambda p_rect: (padding, current_y), "color": self.config.UI_TEXT_COLOR
        })
        current_y += 25 # Approx height of text

        # Bulldozer button
        elements.append({
            "type": "button", "text": "BULLDOZE",
            "rect_func": (lambda y: lambda p_rect: pygame.Rect(padding, y, p_rect.width - 2 * padding, button_height))(current_y),
            "action_func": lambda gs: self._set_tool(gs, "bulldozer"),
            "color_func": lambda gs: self.config.COLOR_RED if gs and gs.current_tool == "bulldozer" else self.config.COLOR_BLUE
        })
        current_y += button_height + button_spacing

        # Building buttons
        for b_key, b_data in self.config.BUILDING_TYPES.items():
            cap_b_key = b_key
            cap_b_data = b_data

            elements.append({
                "type": "button",
                "text_func": lambda gs: f"{cap_b_data['ui_name']} ({cap_b_data['cost']}CR)" if (gs and gs.is_building_unlocked(cap_b_key)) else f"{cap_b_data['ui_name']} (Locked)",
                "rect_func": (lambda y: lambda p_rect: pygame.Rect(padding, y, p_rect.width - 2 * padding, button_height))(current_y),
                "action_func": (lambda key: lambda gs: self._select_building_type(gs, key))(cap_b_key),
                "enabled_func": lambda gs: gs and gs.is_building_unlocked(cap_b_key),
                "color_func": (lambda key, data: lambda gs:
                               self.config.COLOR_AMBER if gs and gs.selected_building_type == key
                               else ( (60,60,60) if not (gs and gs.is_building_unlocked(key) and gs.credits >= data['cost']) else self.config.COLOR_BLUE)
                              )(cap_b_key, cap_b_data)
            })
            current_y += button_height + button_spacing
        return elements

    # --- Action helper methods for buttons ---
    # These will be assigned to button actions and need access to game_state_ref
    # They also need to be defined before being referenced by _define_xxx_panel_elements

    def _set_time_multiplier(self, game_state, multiplier):
        if game_state:
            game_state.time_multiplier = multiplier
            print(f"UI: Time multiplier set to {multiplier}x")
            if hasattr(game_state, 'sound_manager_instance') and game_state.sound_manager_instance:
                game_state.sound_manager_instance.play_sound("ui_click")
            self.refresh_panel_elements_for_state_change() # Refresh UI, e.g. button colors

    def _save_game_action(self, game_state):
        if game_state and self.save_game_func: # save_game_func to be set from main
            self.save_game_func(game_state)

    def _load_game_action(self, game_state):
        if game_state and self.load_game_func: # load_game_func to be set from main
            self.load_game_func(game_state, self) # Pass UIManager for UI refresh after load

    def _set_tool(self, game_state, tool_name):
        if game_state:
            game_state.selected_building_type = None
            game_state.current_tool = tool_name
            print(f"UI: Selected {tool_name} tool.")
            if hasattr(game_state, 'sound_manager_instance') and game_state.sound_manager_instance:
                game_state.sound_manager_instance.play_sound("ui_click")
            self.refresh_panel_elements_for_state_change()

    def _select_building_type(self, game_state, building_key):
        if not game_state: return

        b_data = self.config.BUILDING_TYPES[building_key]
        if not game_state.is_building_unlocked(building_key):
            print(f"UI: {b_data['ui_name']} is locked.")
            if hasattr(game_state, 'sound_manager_instance') and game_state.sound_manager_instance:
                 game_state.sound_manager_instance.play_sound("alert_warning")
            return

        if game_state.credits >= b_data.get('cost', 0):
            game_state.current_tool = None
            game_state.selected_building_type = building_key
            print(f"UI: Selected {building_key} for building.")
            if hasattr(game_state, 'sound_manager_instance') and game_state.sound_manager_instance:
                game_state.sound_manager_instance.play_sound("ui_click")
        else:
            print(f"UI: Cannot select {building_key}, not enough credits.")
            game_state.current_alerts.append(f"Need {b_data.get('cost', 0)} CR for {b_data['ui_name']}")
            if hasattr(game_state, 'sound_manager_instance') and game_state.sound_manager_instance:
                game_state.sound_manager_instance.play_sound("error_credits")
        self.refresh_panel_elements_for_state_change()

    def refresh_panel_elements_for_state_change(self):
        """Re-populates elements for all panels to reflect GameState changes (e.g. button colors)."""
        if not self.game_state_ref: # Cannot refresh if gs_ref is not set
            return
        for panel_key, panel in self.panels.items():
            layout = self.panel_layouts.get(panel_key)
            if layout and hasattr(panel, 'populate_elements'):
                panel.populate_elements(self.game_state_ref)


    def handle_resize(self, new_width, new_height):
        self.screen_width = new_width
        self.screen_height = new_height
        self._create_panels_from_layout() # Re-create panels with new dimensions
        # After re-creating, ensure actions that depend on game_state are correctly set up
        if self.game_state_ref:
            self.set_button_actions_from_game_state(self.game_state_ref)


    def _setup_default_panels(self): # This method is now split into _define_panel_layouts and _create_panels_from_layout
        pass # Kept for compatibility if called, but new methods are primary

    def set_initial_game_state_ref(self, game_state_ref):
        """Sets the game_state reference and fully initializes panels and actions."""
        self.game_state_ref = game_state_ref
        # Re-create panels now that we have game_state_ref for element population
        self._create_panels_from_layout()
        # Then ensure all button actions are correctly wired up
        # self.set_button_actions_from_game_state(game_state_ref) # This is now part of refresh_panel_elements_for_state_change
        self.refresh_panel_elements_for_state_change()


    # Methods like set_build_panel_button_actions and set_time_control_button_actions are now obsolete.
    # Their logic is integrated into _define_xxx_panel_elements and panel.populate_elements called
    # during _create_panels_from_layout, handle_resize, and refresh_panel_elements_for_state_change.

    # The set_button_actions_from_game_state is effectively replaced by calling
    # panel.populate_elements(game_state_ref) for each panel, which re-creates
    # elements including their actions based on the latest game_state_ref.
    # This is done in set_initial_game_state_ref and handle_resize (via _create_panels_from_layout)
    # and in refresh_panel_elements_for_state_change.


    def draw(self, surface, game_state): # game_state here is mainly for alert display timing
        for panel_name, panel in self.panels.items():
            # Panel visibility is handled by panel.is_visible inside panel.draw()
            # if hasattr(panel, 'is_visible') and not panel.is_visible:
            #     continue
            panel.draw(surface, game_state) # Pass game_state if panel elements need it for drawing (e.g. dynamic text)
                                            # Though text is mostly pre-rendered string now.

        # Handle alert display timing
        if self.game_state_ref and self.game_state_ref.current_alerts: # Use stored gs_ref
            self.alert_timer +=1
            if self.alert_timer > (self.config.FPS * 3): # Use config for duration
                self.game_state_ref.current_alerts.pop(0)
                self.alert_timer = 0
        else:
            self.alert_timer = 0 # Reset if no alerts


    def handle_event(self, event, game_state): # game_state is passed for actions
        # Ensure game_state_ref is up-to-date, though actions should use the one captured at creation.
        # This parameter is mostly for consistency if some event handling directly needs it.
        # For button actions, they use the gs_ref captured when they were created/populated.
        if self.game_state_ref != game_state: # Should ideally not happen if setup correctly
            # print("Warning: UIManager.handle_event received different gs than stored gs_ref.")
            pass

        for panel_name, panel in self.panels.items():
            # Panel visibility is handled by panel.handle_event()
            # if hasattr(panel, 'is_visible') and not panel.is_visible:
            #     continue

            if panel.handle_event(event): # This calls the button's action if clicked
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

# Obsolete methods are removed. Their functionality is now part of the panel definition and population logic.

print("UI module loaded.")
