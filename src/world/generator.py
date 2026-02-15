# src/world/generator.py
import opensimplex
import random
from settings import *

class TerrainGenerator:
    def __init__(self, seed):
        self.seed = seed
        self.noise_gen = opensimplex.OpenSimplex(seed)

    def get_pseudo_random(self, x, y, salt=""):
        random.seed(f"{self.seed}_{x}_{y}_{salt}")
        return random.random()

    def _get_raw_pixel(self, x, y):
        """Calculates Base Truth (Used for Map Generation)"""
        # LAYER A: ROOMS
        if self.is_tile_in_room(x, y):
            return 1
        
        # LAYER B: TUNNELS
        raw_noise = self.noise_gen.noise2(x * TUNNEL_FREQ, y * TUNNEL_FREQ)
        if abs(raw_noise) < TUNNEL_THICKNESS:
            return 1 

        return 0 

    def is_tile_in_room(self, x, y):
        """
        [NEW] THE SOURCE OF TRUTH.
        Returns True ONLY if (x,y) is mathematically inside a Round Room.
        Used by the Spawner to enforce the 'Law of the Cavern'.
        """
        cell_x = x // ROOM_GRID_SIZE
        cell_y = y // ROOM_GRID_SIZE
        
        # Check this cell and neighbors for overlapping room circles
        for cy in range(cell_y - 1, cell_y + 2):
            for cx in range(cell_x - 1, cell_x + 2):
                has_room = self.get_pseudo_random(cx, cy, "exist") < ROOM_CHANCE
                if not has_room: continue

                # Deterministic Position & Size
                jitter_x = int(self.get_pseudo_random(cx, cy, "jx") * (ROOM_GRID_SIZE - 2 * ROOM_MAX_RADIUS))
                jitter_y = int(self.get_pseudo_random(cx, cy, "jy") * (ROOM_GRID_SIZE - 2 * ROOM_MAX_RADIUS))
                
                center_x = (cx * ROOM_GRID_SIZE) + ROOM_MAX_RADIUS + jitter_x
                center_y = (cy * ROOM_GRID_SIZE) + ROOM_MAX_RADIUS + jitter_y
                
                radius = ROOM_MIN_RADIUS + (self.get_pseudo_random(cx, cy, "rad") * (ROOM_MAX_RADIUS - ROOM_MIN_RADIUS))

                # Circle Check
                dx = x - center_x
                dy = y - center_y
                if (dx*dx + dy*dy) <= (radius * radius):
                    return True # STRICTLY inside a room
        return False

    def generate_chunk_data(self, chunk_x, chunk_y):
        buffer_size = CHUNK_SIZE + 2
        raw_grid = [[0] * buffer_size for _ in range(buffer_size)]
        
        start_x = (chunk_x * CHUNK_SIZE) - 1
        start_y = (chunk_y * CHUNK_SIZE) - 1

        for y in range(buffer_size):
            for x in range(buffer_size):
                raw_grid[y][x] = self._get_raw_pixel(start_x + x, start_y + y)

        # Cellular Automata Smoothing
        smooth_grid = [row[:] for row in raw_grid]
        for _ in range(SMOOTHING_PASSES):
            temp_grid = [row[:] for row in smooth_grid]
            for y in range(1, buffer_size - 1):
                for x in range(1, buffer_size - 1):
                    wall_count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0: continue
                            if smooth_grid[y+dy][x+dx] == 0:
                                wall_count += 1
                    
                    if wall_count > 4: temp_grid[y][x] = 0
                    elif wall_count < 4: temp_grid[y][x] = 1
            smooth_grid = temp_grid

        final_grid = []
        for y in range(1, CHUNK_SIZE + 1):
            row = []
            for x in range(1, CHUNK_SIZE + 1):
                row.append(smooth_grid[y][x])
            final_grid.append(row)

        return final_grid