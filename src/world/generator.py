# src/world/generator.py
import numpy as np
import noise 
from settings import *

class AtlasGenerator:
    def __init__(self, seed):
        self.seed = seed

    def generate_chunk(self, cx, cy):
        """
        Generates a chunk using Global Integer Coordinates.
        Seamless noise generation using constants from settings.py.
        """
        # 1. Create Integer Ranges
        local_x = np.arange(CHUNK_SIZE)
        local_y = np.arange(CHUNK_SIZE)
        
        # 2. Convert to Global World Coordinates
        global_x = (cx * CHUNK_SIZE) + local_x
        global_y = (cy * CHUNK_SIZE) + local_y
        
        # 3. Apply Scale
        scaled_x = global_x * SCALE
        scaled_y = global_y * SCALE
        
        # 4. Generate Noise Loop
        chunk_data = np.zeros((CHUNK_SIZE, CHUNK_SIZE))

        for i, y_val in enumerate(scaled_y):
            row_noise = [noise.snoise2(x_val, y_val, 
                                       octaves=OCTAVES, 
                                       persistence=PERSISTENCE, 
                                       lacunarity=LACUNARITY, 
                                       base=self.seed) for x_val in scaled_x]
            chunk_data[i] = row_noise
            
        # 5. Apply Modifiers (Invert & Sharpen)
        # MATCHES generate_map.py EXACTLY
        height_map = chunk_data * -1.2
        
        # 6. Biome Classification (Using Settings Constants)
        biome_map = np.full((CHUNK_SIZE, CHUNK_SIZE), BIOME_OCEAN, dtype=int)
        
        # Deep Ocean
        biome_map[height_map < -0.05] = BIOME_DEEP_OCEAN
        
        # Land Layers
        biome_map[height_map > BEACH_LEVEL] = BIOME_BEACH
        biome_map[height_map > GRASS_LEVEL] = BIOME_GRASS
        biome_map[height_map > FOREST_LEVEL] = BIOME_FOREST
        
        # Mountain Layers
        biome_map[height_map > MTN_LOW_LEVEL] = BIOME_MTN_LOW
        biome_map[height_map > MTN_MID_LEVEL] = BIOME_MTN_MID
        biome_map[height_map > MTN_HIGH_LEVEL] = BIOME_MTN_HIGH

        # 7. Transpose for Pygame (x, y)
        return biome_map.T

    def find_spawn_point(self):
        """Finds a safe spawn point on Grass."""
        print("Scanning for Safe Spawn...")
        # Check outward from 0,0 in 320 pixel steps (10 tiles)
        for r in range(0, 5000, 10):
            x_pixel = r * TILE_SIZE
            y_pixel = 0
            
            x_noise = x_pixel * SCALE
            y_noise = 0
            
            # Use EXACT same math
            h = noise.snoise2(x_noise, y_noise, octaves=OCTAVES, base=self.seed) * -1.2
            
            # Spawn if valid grass
            if h > GRASS_LEVEL and h < FOREST_LEVEL: 
                return x_pixel, y_pixel
                
        return 0, 0