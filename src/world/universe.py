# src/world/universe.py
import pygame
from settings import *
from world.world import WorldManager, WorldChunk
from world.generator import AtlasGenerator
from world.cave_generator import CaveGenerator

class UniverseManager:
    """
    Manages the 'Multiverse': The Surface World and the Underworld.
    Handles switching between layers seamlessly.
    """
    def __init__(self):
        # Layer 0: The Surface (Islands)
        self.surface_generator = AtlasGenerator(SEED)
        self.surface_chunks = {}
        
        # Layer -1: The Underworld (Caves)
        self.cave_generator = CaveGenerator(SEED)
        self.cave_chunks = {}
        
        # State
        self.current_layer = 0 # 0 = Surface, -1 = Cave
        
    @property
    def current_chunks(self):
        """Returns the chunk dictionary for the active layer."""
        if self.current_layer == 0:
            return self.surface_chunks
        else:
            return self.cave_chunks

    @property
    def active_generator(self):
        if self.current_layer == 0:
            return self.surface_generator
        else:
            return self.cave_generator

    def get_chunk(self, cx, cy):
        """Retrieves a chunk for the ACTIVE layer."""
        chunks = self.current_chunks
        
        if (cx, cy) not in chunks:
            # Generate new data using the correct generator
            if self.current_layer == 0:
                grid = self.surface_generator.generate_chunk(cx, cy)
            else:
                grid = self.cave_generator.generate_chunk(cx, cy)
                
            chunks[(cx, cy)] = WorldChunk(cx, cy, grid)
            
        return chunks[(cx, cy)]

    def toggle_layer(self):
        """Debug function to instantly swap dimensions."""
        if self.current_layer == 0:
            self.current_layer = -1
            print("🌑 Entering the Underworld...")
        else:
            self.current_layer = 0
            print("☀️ Returning to Surface...")

    # --- WRAPPER FUNCTIONS (So Main.py doesn't break) ---
    # These match the exact function names from your old WorldManager
    
    def get_nearby_walls(self, player_rect):
        """Standard collision check, but asks the active layer."""
        walls = []
        center_cx = int(player_rect.centerx // (CHUNK_SIZE * TILE_SIZE))
        center_cy = int(player_rect.centery // (CHUNK_SIZE * TILE_SIZE))
        
        for cy in range(center_cy - 1, center_cy + 2):
            for cx in range(center_cx - 1, center_cx + 2):
                chunk = self.get_chunk(cx, cy)
                for r in range(CHUNK_SIZE):
                    for c in range(CHUNK_SIZE):
                        tile_id = chunk.grid[r][c] 
                        if tile_id in COLLISION_TILES:
                            px = (cx * CHUNK_SIZE + r) * TILE_SIZE
                            py = (cy * CHUNK_SIZE + c) * TILE_SIZE
                            walls.append(pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))
        return walls

    def draw_visible_chunks(self, screen, camera):
        """Draws the active layer."""
        cam_x = -camera.camera.x
        cam_y = -camera.camera.y
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        chunk_px_w = CHUNK_SIZE * TILE_SIZE
        
        start_cx = int(cam_x // chunk_px_w)
        start_cy = int(cam_y // chunk_px_w)
        end_cx = int((cam_x + screen_w) // chunk_px_w) + 1
        end_cy = int((cam_y + screen_h) // chunk_px_w) + 1
        
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                chunk = self.get_chunk(cx, cy)
                chunk_x_offset = cx * chunk_px_w
                chunk_y_offset = cy * chunk_px_w
                
                for x in range(CHUNK_SIZE):
                    for y in range(CHUNK_SIZE):
                        tile_id = chunk.grid[x][y]
                        # Optimization: Don't draw deep ocean or cave walls (if we want pure black)
                        if tile_id == BIOME_DEEP_OCEAN: continue 

                        dest_x = chunk_x_offset + (x * TILE_SIZE) + camera.camera.x
                        dest_y = chunk_y_offset + (y * TILE_SIZE) + camera.camera.y
                        
                        if -TILE_SIZE <= dest_x < screen_w and -TILE_SIZE <= dest_y < screen_h:
                            color = BIOME_COLORS.get(tile_id, (255, 0, 255))
                            pygame.draw.rect(screen, color, (dest_x, dest_y, TILE_SIZE, TILE_SIZE))