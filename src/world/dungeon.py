# src/world/dungeon.py
import pygame
from settings import *
from world.generator import TerrainGenerator

class Chunk:
    def __init__(self, chunk_x, chunk_y, generator):
        self.cx = chunk_x
        self.cy = chunk_y
        self.rects = [] 

        # Call the new "Buffered Generator" to get the whole grid at once
        # This handles the Cellular Automata math internally
        self.grid = generator.generate_chunk_data(chunk_x, chunk_y)

        # Build Rects for Physics/Rendering
        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                if self.grid[y][x] == 0: # Wall
                    # Calculate Global Position
                    rect_x = (chunk_x * CHUNK_SIZE + x) * TILE_SIZE
                    rect_y = (chunk_y * CHUNK_SIZE + y) * TILE_SIZE
                    self.rects.append(pygame.Rect(rect_x, rect_y, TILE_SIZE, TILE_SIZE))

class DungeonManager:
    def __init__(self):
        self.generator = TerrainGenerator(SEED)
        self.chunks = {} 

    def get_chunk(self, x, y):
        if (x, y) not in self.chunks:
            self.chunks[(x, y)] = Chunk(x, y, self.generator)
        return self.chunks[(x, y)]

    def draw_visible_chunks(self, screen, camera):
        start_chunk_x = int(camera.offset.x // (CHUNK_SIZE * TILE_SIZE))
        start_chunk_y = int(camera.offset.y // (CHUNK_SIZE * TILE_SIZE))
        
        # Increased range slightly to prevent "pop-in" at edges
        for y in range(start_chunk_y - 1, start_chunk_y + 3):
            for x in range(start_chunk_x - 1, start_chunk_x + 3):
                chunk = self.get_chunk(x, y)
                for wall_rect in chunk.rects:
                    draw_rect = camera.apply(wall_rect)
                    # Draw only if on screen (Optimization)
                    if draw_rect.colliderect(screen.get_rect()):
                        pygame.draw.rect(screen, (50, 40, 60), draw_rect)

    def get_nearby_walls(self, player_rect):
        walls = []
        p_chunk_x = int(player_rect.centerx // (CHUNK_SIZE * TILE_SIZE))
        p_chunk_y = int(player_rect.centery // (CHUNK_SIZE * TILE_SIZE))
        
        for y in range(p_chunk_y - 1, p_chunk_y + 2):
            for x in range(p_chunk_x - 1, p_chunk_x + 2):
                chunk = self.get_chunk(x, y)
                walls.extend(chunk.rects)
        return walls