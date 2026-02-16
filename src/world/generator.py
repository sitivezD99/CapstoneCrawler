# src/world/generator.py
import numpy as np
import noise
from settings import *

class AtlasGenerator:
    def __init__(self, seed):
        self.seed = seed
        
        # --- THE "DNA" OF THE WORLD ---
        self.gen_scale = 0.0002   
        self.octaves = 4          
        self.persistence = 0.3    
        self.lacunarity = 2.0     

    def generate_grid(self, start_x, start_y, width, height):
        """
        Generates a 2D biome grid using Tile Coordinates.
        """
        local_x = np.arange(width, dtype=np.float32)
        local_y = np.arange(height, dtype=np.float32)
        
        global_y_vals = (start_y + local_y) * self.gen_scale
        global_x_vals = (start_x + local_x) * self.gen_scale
        
        biome_grid = np.zeros((height, width), dtype=np.int32)
        
        # Use the Global Constant
        land_start_threshold = LAND_THRESHOLD 

        for i, y_val in enumerate(global_y_vals):
            row_noise = [noise.snoise2(x_val, y_val, 
                                       octaves=self.octaves, 
                                       persistence=self.persistence, 
                                       lacunarity=self.lacunarity, 
                                       base=self.seed) for x_val in global_x_vals]
            
            row_noise = np.array(row_noise, dtype=np.float32)

            # --- CUBIC TRANSFORM ---
            height_map = row_noise * row_noise * row_noise
            height_map *= 4.0
            
            # --- BIOME CLASSIFICATION ---
            row_biomes = np.full(width, BIOME_OCEAN, dtype=np.int32)
            
            # Water Layers
            row_biomes[height_map < 0.00] = BIOME_DEEP_OCEAN
            row_biomes[height_map > 0.08] = BIOME_SHALLOW_WATER
            
            # Land Layers
            row_biomes[height_map > land_start_threshold] = BIOME_BEACH
            row_biomes[height_map > (land_start_threshold + 0.02)] = BIOME_GRASS
            
            # Elevation Layers
            row_biomes[height_map > 0.35] = BIOME_FOREST
            row_biomes[height_map > 0.8] = BIOME_MTN_LOW
            row_biomes[height_map > 1.0] = BIOME_MTN_MID
            row_biomes[height_map > 1.3] = BIOME_MTN_HIGH
            
            biome_grid[i] = row_biomes

        return biome_grid

    def generate_chunk(self, cx, cy):
        """Game wrapper: Requests a specific 32x32 chunk."""
        grid = self.generate_grid(cx * CHUNK_SIZE, cy * CHUNK_SIZE, CHUNK_SIZE, CHUNK_SIZE)
        return grid.T

    def find_spawn_point(self):
        """
        PROFESSIONAL SPAWN SEARCH: SPIRAL ALGORITHM
        Fixed: Now correctly converts Pixels -> Tiles before checking noise.
        """
        print("🌍 Scanning for valid spawn point...")
        
        # Spiral Search Pattern variables
        x, y = 0, 0
        dx, dy = 0, -1
        
        # Scan up to 1000 chunks out
        for i in range(1000**2):
            # 1. Calculate the Pixel Center of this chunk (For the Player)
            chunk_pixel_x = x * CHUNK_SIZE * TILE_SIZE + (CHUNK_SIZE * TILE_SIZE // 2)
            chunk_pixel_y = y * CHUNK_SIZE * TILE_SIZE + (CHUNK_SIZE * TILE_SIZE // 2)
            
            # 2. Calculate the Noise Coordinate (For the Generator)
            # CRITICAL FIX: Divide by TILE_SIZE to get Grid Coordinates
            nx = (chunk_pixel_x / TILE_SIZE) * self.gen_scale
            ny = (chunk_pixel_y / TILE_SIZE) * self.gen_scale
            
            # 3. Check Noise
            n = noise.snoise2(nx, ny, octaves=self.octaves, persistence=self.persistence, base=self.seed)
            h = n * n * n * 4.0
            
            # 4. Check if it's solid land (Grass level or higher)
            # We add a buffer (+0.05) to ensure we don't spawn on the water's edge
            if h > (LAND_THRESHOLD + 0.05): 
                print(f"✅ Land found at Chunk [{x}, {y}] (Noise Val: {h:.2f}).")
                return chunk_pixel_x, chunk_pixel_y

            # Spiral Logic (Move to next chunk)
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1-y):
                dx, dy = -dy, dx
            x, y = x+dx, y+dy
            
        print("⚠️ WARNING: No land found. Spawning at 0,0.")
        return 0, 0