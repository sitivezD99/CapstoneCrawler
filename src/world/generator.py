# src/world/generator.py
import numpy as np
import noise
import random
from settings import *

class AtlasGenerator:
    def __init__(self, seed):
        self.seed = seed
        self.gen_scale = CONTINENT_SCALE   
        self.octaves = OCTAVES          
        self.persistence = PERSISTENCE    
        self.lacunarity = LACUNARITY     

    def generate_grid(self, start_x, start_y, width, height):
        local_x = np.arange(width, dtype=np.float32)
        local_y = np.arange(height, dtype=np.float32)
        
        global_y_vals = (start_y + local_y) * self.gen_scale
        global_x_vals = (start_x + local_x) * self.gen_scale
        
        biome_grid = np.zeros((height, width), dtype=np.int32)
        
        land_start_threshold = LAND_THRESHOLD 

        for i, y_val in enumerate(global_y_vals):
            # 1. ELEVATION NOISE (Continent Shape)
            row_noise = [noise.snoise2(x_val, y_val, 
                                       octaves=self.octaves, 
                                       persistence=self.persistence, 
                                       lacunarity=self.lacunarity, 
                                       base=self.seed) for x_val in global_x_vals]
            
            height_map = np.array(row_noise, dtype=np.float32)

            # Cubic Transform (Your original continent math)
            height_map = height_map * height_map * height_map
            height_map *= 4.0
            
            # --- BIOME CLASSIFICATION ---
            row_biomes = np.full(width, BIOME_OCEAN, dtype=np.int32)
            
            # Water
            row_biomes[height_map < 0.00] = BIOME_DEEP_OCEAN
            row_biomes[height_map > 0.08] = BIOME_SHALLOW_WATER
            
            # Land Masks
            is_land = height_map > land_start_threshold
            
            # --- ZONING LOGIC ---
            # Zone 1: Lowlands (Between Beach and Highlands)
            is_low_zone = (height_map > (land_start_threshold + 0.02)) & (height_map <= HIGHLAND_THRESHOLD)
            
            # Zone 2: Highlands (Between Lowlands and Mountains)
            is_high_zone = (height_map > HIGHLAND_THRESHOLD) & (height_map <= 0.8)
            
            # Apply Beach
            row_biomes[is_land] = BIOME_BEACH
            
            # Apply Standard Lowlands (Meadow)
            row_biomes[is_low_zone] = BIOME_L_MEADOW
            
            # Apply Standard Highlands (Forest)
            row_biomes[is_high_zone] = BIOME_H_FOREST
            
            # --- MOUNTAINS ---
            row_biomes[height_map > 0.8] = BIOME_MTN_LOW
            row_biomes[height_map > 1.0] = BIOME_MTN_HIGH
            row_biomes[height_map > 1.3] = BIOME_MTN_PEAK
            
            # NOTE: No Object Generation Loop Here!
            # The code ends here, ensuring plain vanilla tiles.
            
            biome_grid[i] = row_biomes

        return biome_grid

    def generate_chunk(self, cx, cy):
        grid = self.generate_grid(cx * CHUNK_SIZE, cy * CHUNK_SIZE, CHUNK_SIZE, CHUNK_SIZE)
        return grid.T

    def find_spawn_point(self):
        print("🌍 Scanning for valid spawn point...")
        x, y = 0, 0
        dx, dy = 0, -1
        
        for i in range(1000**2):
            chunk_pixel_x = x * CHUNK_SIZE * TILE_SIZE + (CHUNK_SIZE * TILE_SIZE // 2)
            chunk_pixel_y = y * CHUNK_SIZE * TILE_SIZE + (CHUNK_SIZE * TILE_SIZE // 2)
            
            nx = (chunk_pixel_x / TILE_SIZE) * self.gen_scale
            ny = (chunk_pixel_y / TILE_SIZE) * self.gen_scale
            
            n = noise.snoise2(nx, ny, octaves=self.octaves, persistence=self.persistence, base=self.seed)
            h = n * n * n * 4.0
            
            if h > (LAND_THRESHOLD + 0.05): 
                print(f"✅ Land found at Chunk [{x}, {y}] (Noise Val: {h:.2f}).")
                return chunk_pixel_x, chunk_pixel_y

            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1-y):
                dx, dy = -dy, dx
            x, y = x+dx, y+dy
            
        print("⚠️ WARNING: No land found. Spawning at 0,0.")
        return 0, 0