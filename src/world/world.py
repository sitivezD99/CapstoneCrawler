# src/world/world.py
import pygame
from settings import *
from world.generator import AtlasGenerator

class WorldChunk:
    """
    A container for a specific 32x32 section of the world.
    This is the foundational block for your future systems (Entities, Loot, Buildings).
    """
    def __init__(self, cx, cy, grid_data):
        self.cx = cx
        self.cy = cy
        self.grid = grid_data  # The numpy array lives here now
        
        # Future-proofing:
        self.has_village = False 
        self.entities = [] 

class WorldManager:
    def __init__(self):
        self.generator = AtlasGenerator(SEED)
        self.chunks = {} 

    def get_chunk(self, cx, cy):
        """Retrieves a chunk object, generating it if it doesn't exist."""
        if (cx, cy) not in self.chunks:
            # Generate the raw data
            grid = self.generator.generate_chunk(cx, cy)
            # Wrap it in our Smart Object
            self.chunks[(cx, cy)] = WorldChunk(cx, cy, grid)
            
        return self.chunks[(cx, cy)]

    def get_nearby_walls(self, player_rect):
        """
        Returns a list of Rects for physics collision.
        """
        walls = []
        
        center_cx = int(player_rect.centerx // (CHUNK_SIZE * TILE_SIZE))
        center_cy = int(player_rect.centery // (CHUNK_SIZE * TILE_SIZE))
        
        for cy in range(center_cy - 1, center_cy + 2):
            for cx in range(center_cx - 1, center_cx + 2):
                chunk = self.get_chunk(cx, cy)
                
                # Iterate through local tiles
                for r in range(CHUNK_SIZE):
                    for c in range(CHUNK_SIZE):
                        # Access the grid inside the object
                        tile_id = chunk.grid[r][c] 
                        
                        if tile_id in COLLISION_TILES:
                            px = (cx * CHUNK_SIZE + r) * TILE_SIZE
                            py = (cy * CHUNK_SIZE + c) * TILE_SIZE
                            walls.append(pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))
        return walls

    def draw_visible_chunks(self, screen, camera):
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
                        # Access the grid inside the object
                        tile_id = chunk.grid[x][y]
                        
                        if tile_id == BIOME_DEEP_OCEAN: continue # Optimization: Don't draw deep ocean

                        dest_x = chunk_x_offset + (x * TILE_SIZE) + camera.camera.x
                        dest_y = chunk_y_offset + (y * TILE_SIZE) + camera.camera.y
                        
                        if -TILE_SIZE <= dest_x < screen_w and -TILE_SIZE <= dest_y < screen_h:
                            color = BIOME_COLORS.get(tile_id, (255, 0, 255))
                            pygame.draw.rect(screen, color, (dest_x, dest_y, TILE_SIZE, TILE_SIZE))