# src/world/world.py
import pygame
from settings import *

class WorldChunk:
    def __init__(self, chunk_x, chunk_y, grid_data):
        self.cx = chunk_x
        self.cy = chunk_y
        self.grid = grid_data
        self.rects = [] 
        
        # Build the initial collision mesh
        self.build_collision_mesh()

    def build_collision_mesh(self):
        """
        Constructs the list of solid walls for physics.
        We make this a separate function so we can call it again later!
        """
        self.rects = [] # Clear old collisions
        
        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                tile_id = self.grid[x][y]
                
                # Check against the Global Collision Set
                if tile_id in COLLISION_TILES:
                    # Calculate Global Position
                    rect_x = (self.cx * CHUNK_SIZE + x) * TILE_SIZE
                    rect_y = (self.cy * CHUNK_SIZE + y) * TILE_SIZE
                    self.rects.append(pygame.Rect(rect_x, rect_y, TILE_SIZE, TILE_SIZE))

    def rebuild(self):
        """
        Call this whenever you modify self.grid manually (like drilling or doormats).
        It forces the physics engine to acknowledge the changes.
        """
        self.build_collision_mesh()

class WorldManager:
    # This legacy class might not be used anymore if you switched to UniverseManager,
    # but we keep it just in case to prevent import errors.
    def __init__(self):
        self.chunks = {}