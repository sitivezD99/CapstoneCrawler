import pygame
from settings import *
from world.generator import TerrainGenerator

class Chunk:
    def __init__(self, chunk_x, chunk_y, generator):
        self.cx = chunk_x
        self.cy = chunk_y
        self.grid = [] # 2D array for this chunk
        self.rects = [] # Optimization: Pre-calculated rects for rendering

        # Generate Data for this specific 32x32 area
        for y in range(CHUNK_SIZE):
            row = []
            for x in range(CHUNK_SIZE):
                # Convert local chunk coordinate to global world coordinate
                global_x = (chunk_x * CHUNK_SIZE) + x
                global_y = (chunk_y * CHUNK_SIZE) + y
                
                tile = generator.get_tile_at(global_x, global_y)
                row.append(tile)
                
                # If it's a wall, save the rect for physics/rendering
                if tile == 0:
                    rect_x = global_x * TILE_SIZE
                    rect_y = global_y * TILE_SIZE
                    self.rects.append(pygame.Rect(rect_x, rect_y, TILE_SIZE, TILE_SIZE))
            self.grid.append(row)

class DungeonManager:
    def __init__(self):
        self.generator = TerrainGenerator(SEED)
        self.chunks = {} # Dictionary: {(x,y): ChunkObject}

    def get_chunk(self, x, y):
        """Return chunk if exists, else generate it."""
        if (x, y) not in self.chunks:
            self.chunks[(x, y)] = Chunk(x, y, self.generator)
        return self.chunks[(x, y)]

    def draw_visible_chunks(self, screen, camera):
        # Calculate which chunks are visible based on camera position
        start_chunk_x = int(camera.offset.x // (CHUNK_SIZE * TILE_SIZE))
        start_chunk_y = int(camera.offset.y // (CHUNK_SIZE * TILE_SIZE))

        # Loop through visible chunks (plus a buffer of 1)
        for y in range(start_chunk_y - 1, start_chunk_y + 3):
            for x in range(start_chunk_x - 1, start_chunk_x + 3):
                chunk = self.get_chunk(x, y)
                
                # Draw Walls in this chunk
                for wall_rect in chunk.rects:
                    # Apply Camera Offset
                    draw_rect = camera.apply(wall_rect)
                    pygame.draw.rect(screen, (50, 40, 60), draw_rect) # Dark Rock Color

    def get_nearby_walls(self, player_rect):
        """Optimization: Only get walls from the chunks touching the player"""
        walls = []
        # Calculate which chunk the player is in
        p_chunk_x = int(player_rect.centerx // (CHUNK_SIZE * TILE_SIZE))
        p_chunk_y = int(player_rect.centery // (CHUNK_SIZE * TILE_SIZE))
        
        # Get walls from current and neighbor chunks
        for y in range(p_chunk_y - 1, p_chunk_y + 2):
            for x in range(p_chunk_x - 1, p_chunk_x + 2):
                chunk = self.get_chunk(x, y)
                walls.extend(chunk.rects)
        return walls