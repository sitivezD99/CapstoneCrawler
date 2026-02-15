# src/world/generator.py
import opensimplex
import random
from settings import *

class TerrainGenerator:
    def __init__(self, seed):
        self.seed = seed
        self.noise_gen = opensimplex.OpenSimplex(seed)

    def get_pseudo_random(self, x, y, salt=""):
        """
        Deterministic random number generator based on coordinates.
        Returns float 0.0 to 1.0
        """
        random.seed(f"{self.seed}_{x}_{y}_{salt}")
        return random.random()

    def _get_raw_pixel(self, x, y):
        """
        Calculates the 'Base Truth' of a specific coordinate 
        BEFORE any smoothing is applied.
        Returns: 1 (Floor) or 0 (Wall)
        """
        # --- LAYER A: ROOM NODES (Spatial Grid Logic) ---
        # Determine which "Coarse Cell" this pixel belongs to
        cell_x = x // ROOM_GRID_SIZE
        cell_y = y // ROOM_GRID_SIZE
        
        # We must check the current cell AND neighbor cells
        # because a room in a neighbor cell might overlap into this one.
        is_room = False
        
        for cy in range(cell_y - 1, cell_y + 2):
            for cx in range(cell_x - 1, cell_x + 2):
                # 1. Check if this cell actually HAS a room
                has_room = self.get_pseudo_random(cx, cy, "exist") < ROOM_CHANCE
                if not has_room:
                    continue

                # 2. Determine Room Center & Size (Deterministic Jitter)
                jitter_x = int(self.get_pseudo_random(cx, cy, "jx") * (ROOM_GRID_SIZE - 2 * ROOM_MAX_RADIUS))
                jitter_y = int(self.get_pseudo_random(cx, cy, "jy") * (ROOM_GRID_SIZE - 2 * ROOM_MAX_RADIUS))
                
                center_x = (cx * ROOM_GRID_SIZE) + ROOM_MAX_RADIUS + jitter_x
                center_y = (cy * ROOM_GRID_SIZE) + ROOM_MAX_RADIUS + jitter_y
                
                radius = ROOM_MIN_RADIUS + (self.get_pseudo_random(cx, cy, "rad") * (ROOM_MAX_RADIUS - ROOM_MIN_RADIUS))

                # 3. Distance Check (Circle Math)
                dx = x - center_x
                dy = y - center_y
                if (dx*dx + dy*dy) <= (radius * radius):
                    is_room = True
                    break # Optimization: If we are in one room, we are good.
        
        if is_room:
            return 1 # Floor

        # --- LAYER B: WORM TUNNELS (Ridged Noise) ---
        # Only check tunnels if it's not already a room
        raw_noise = self.noise_gen.noise2(x * TUNNEL_FREQ, y * TUNNEL_FREQ)
        # "Ridged" means taking the absolute value to get a sharp crease at 0
        tunnel_val = abs(raw_noise)
        
        if tunnel_val < TUNNEL_THICKNESS:
            return 1 # Floor

        return 0 # Wall

    def generate_chunk_data(self, chunk_x, chunk_y):
        """
        Generates the final 32x32 grid for a chunk, applying
        Cellular Automata smoothing seamlessly.
        """
        # 1. Generate Buffer Grid (34x34)
        # We need the 1-tile border of neighbors to smooth the edges correctly.
        buffer_size = CHUNK_SIZE + 2
        raw_grid = [[0] * buffer_size for _ in range(buffer_size)]
        
        start_x = (chunk_x * CHUNK_SIZE) - 1
        start_y = (chunk_y * CHUNK_SIZE) - 1

        for y in range(buffer_size):
            for x in range(buffer_size):
                raw_grid[y][x] = self._get_raw_pixel(start_x + x, start_y + y)

        # 2. Apply Cellular Automata (Erosion)
        # Rule: If a tile has > 4 wall neighbors, it becomes a wall.
        # This removes "single pixel islands" and smooths jagged noise.
        smooth_grid = [row[:] for row in raw_grid] # Copy

        for _ in range(SMOOTHING_PASSES):
            temp_grid = [row[:] for row in smooth_grid]
            for y in range(1, buffer_size - 1):
                for x in range(1, buffer_size - 1):
                    # Count Wall Neighbors (0 is wall)
                    wall_count = 0
                    # 3x3 loop around pixel
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0: continue
                            if smooth_grid[y+dy][x+dx] == 0:
                                wall_count += 1
                    
                    # Apply 4-5 Rule
                    if wall_count > 4:
                        temp_grid[y][x] = 0 # Become Wall
                    elif wall_count < 4:
                        temp_grid[y][x] = 1 # Become Floor
            smooth_grid = temp_grid

        # 3. Extract the Center 32x32 (Crop the buffer)
        final_grid = []
        for y in range(1, CHUNK_SIZE + 1):
            row = []
            for x in range(1, CHUNK_SIZE + 1):
                row.append(smooth_grid[y][x])
            final_grid.append(row)

        return final_grid