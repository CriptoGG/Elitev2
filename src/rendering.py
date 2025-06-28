# Rendering engine for Sci-Fi City Builder
# Focus on wireframe and minimalist Elite 1984 style

import pygame

# Placeholder for rendering functions
# This will be expanded significantly

def init_display(width, height, caption="Sci-Fi City Builder"):
    """Initializes the Pygame display."""
    pygame.init()
    # Add pygame.RESIZABLE flag to allow window resizing
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    pygame.display.set_caption(caption)
    print(f"Display initialized: {width}x{height} (Resizable)")
    return screen

def draw_wireframe_rect(surface, color, rect, thickness=1):
    """Draws a wireframe rectangle."""
    pygame.draw.rect(surface, color, rect, thickness)

def draw_text(surface, text, position, font, color):
    """Renders and draws text on the surface."""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)

# Example: Drawing a basic grid (conceptual)
def draw_grid(surface, grid_width, grid_height, tile_size, color):
    """Draws a simple wireframe grid."""
    for x in range(0, grid_width * tile_size, tile_size):
        pygame.draw.line(surface, color, (x, 0), (x, grid_height * tile_size))
    for y in range(0, grid_height * tile_size, tile_size):
        pygame.draw.line(surface, color, (0, y), (grid_width * tile_size, y))

# Placeholder for drawing buildings (will become more complex)
def draw_building(surface, building_type, position, color):
    """Draws a placeholder for a building."""
    # For now, just a colored square
    rect = pygame.Rect(position[0], position[1], 32, 32) # Assuming 32x32 tile size
    draw_wireframe_rect(surface, color, rect, 2)
    # In future, this would involve more complex wireframe shapes based on building_type

def draw_ui_panel(surface, screen_height, panel_height, color):
    """Draws the bottom UI panel."""
    panel_rect = pygame.Rect(0, screen_height - panel_height, surface.get_width(), panel_height)
    pygame.draw.rect(surface, color, panel_rect) # Solid panel for now
    draw_wireframe_rect(surface, (100,100,100), panel_rect, 1) # Border

def draw_resource_nodes(surface, game_state, tile_size, camera_offset_x, camera_offset_y, config_ref):
    """Draws resource nodes on the grid."""
    for r_idx, row in enumerate(game_state.resource_grid):
        for c_idx, node_type_key in enumerate(row):
            if node_type_key:
                node_config = config_ref.RESOURCE_NODE_TYPES.get(node_type_key)
                if node_config:
                    color = node_config.get("color", (255,255,255)) # Default to white if no color

                    # Small rect in the center of the tile for the node
                    node_rect_size = tile_size // 3
                    node_rect_x = c_idx * tile_size + (tile_size - node_rect_size) // 2 - camera_offset_x
                    node_rect_y = r_idx * tile_size + (tile_size - node_rect_size) // 2 - camera_offset_y

                    node_screen_rect = pygame.Rect(node_rect_x, node_rect_y, node_rect_size, node_rect_size)

                    # Only draw if on screen (basic culling)
                    if node_screen_rect.colliderect(surface.get_rect()):
                         pygame.draw.rect(surface, color, node_screen_rect, 0) # Filled rect for node


# More functions will be added for:
# - Drawing specific building wireframes
# - Handling camera/viewport for scrolling
# - Special effects (e.g., lines for power conduits)

print("Rendering module loaded.")
