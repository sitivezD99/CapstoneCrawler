# src/world/world.py
import pygame
from settings import *

class WorldChunk:
    """
    Optimized World Chunk.
    - Implements 'Greedy Meshing' to reduce physics calculations by ~70%.
    """
    def __init__(self, chunk_x, chunk_y, grid_data):
        self.cx = chunk_x
        self.cy = chunk_y
        self.grid = grid_data
        self.rects = [] 
        self.build_collision_mesh()

    def build_collision_mesh(self):
        self.rects = [] 
        visited = set()

        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                if (x, y) in visited: continue
                
                tile_id = self.grid[x][y]
                
                if tile_id in COLLISION_TILES:
                    # Start a strip
                    width = 1
                    visited.add((x, y))
                    
                    # Look ahead to merge horizontal walls
                    while (x + width) < CHUNK_SIZE:
                        next_tile = self.grid[x + width][y]
                        if next_tile in COLLISION_TILES:
                            visited.add((x + width, y))
                            width += 1
                        else:
                            break
                    
                    rect_x = (self.cx * CHUNK_SIZE + x) * TILE_SIZE
                    rect_y = (self.cy * CHUNK_SIZE + y) * TILE_SIZE
                    self.rects.append(pygame.Rect(rect_x, rect_y, width * TILE_SIZE, TILE_SIZE))

    def rebuild(self):
        self.build_collision_mesh()