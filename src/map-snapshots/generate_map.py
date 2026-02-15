import os
# Silence Pygame support prompt
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import sys
import time
import datetime  # <--- NEW IMPORT for timestamps
import numpy as np
import pygame
import multiprocessing
from multiprocessing import shared_memory
import noise

# --- 1. PATH SETUP ---
# Get the directory where this script lives (src/map-snapshots)
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (src) so we can import settings
src_dir = os.path.dirname(current_script_dir)
sys.path.append(src_dir)

from settings import *
from world.generator import AtlasGenerator

# --- CONFIGURATION ---
MAP_WIDTH = 10000   # 10k x 10k = 100 Million Tiles (Huge!)
MAP_HEIGHT = 10000  
CHUNK_BATCH = 100   # Processing batch size

def worker_task(args):
    y_start_idx, shm_name, shape, seed, start_x_offset, start_y_offset = args
    
    # Attach to shared memory
    shm = shared_memory.SharedMemory(name=shm_name)
    full_image = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
    
    # Palette Setup (Fast Lookup)
    fast_palette = np.zeros((256, 3), dtype=np.uint8)
    for k, v in BIOME_COLORS.items():
        fast_palette[k] = v

    y_start_local = y_start_idx * CHUNK_BATCH
    y_end_local = min(y_start_local + CHUNK_BATCH, MAP_HEIGHT)
    height_of_strip = y_end_local - y_start_local
    
    # Global Coordinates Calculation
    # We generate the map AROUND the player
    global_x_coords = (np.arange(MAP_WIDTH) + start_x_offset) * SCALE
    global_y_start = (y_start_local + start_y_offset)
    
    strip_indices = np.zeros((MAP_WIDTH, height_of_strip), dtype=np.uint8)
    
    for i, global_y in enumerate(range(y_end_local - y_start_local)):
        real_y_index = global_y_start + i
        real_y = real_y_index * SCALE
        
        # --- NOISE MATH (Synced with Game) ---
        row_noise = [noise.snoise2(x, real_y, octaves=OCTAVES, persistence=PERSISTENCE, lacunarity=LACUNARITY, base=seed) 
                     for x in global_x_coords]
        
        row_noise = np.array(row_noise)
        row_noise = row_noise * -1.2 # Invert/Sharpen modifier
        
        # Classify Biomes
        row_indices = np.full(MAP_WIDTH, BIOME_OCEAN, dtype=np.uint8)
        
        row_indices[row_noise < -0.05] = BIOME_DEEP_OCEAN
        row_indices[row_noise > BEACH_LEVEL] = BIOME_BEACH
        row_indices[row_noise > GRASS_LEVEL] = BIOME_GRASS
        row_indices[row_noise > FOREST_LEVEL] = BIOME_FOREST
        row_indices[row_noise > MTN_LOW_LEVEL] = BIOME_MTN_LOW
        row_indices[row_noise > MTN_MID_LEVEL] = BIOME_MTN_MID
        row_indices[row_noise > MTN_HIGH_LEVEL] = BIOME_MTN_HIGH
                
        strip_indices[:, i] = row_indices

    # Map indices to RGB colors
    strip_rgb = fast_palette[strip_indices]
    
    # Write to shared memory buffer
    full_image[:, y_start_local:y_end_local] = strip_rgb
    shm.close()

if __name__ == "__main__":
    print(f"--- 📸 MAP SNAPSHOT TOOL ---")
    print(f"Resolution: {MAP_WIDTH}x{MAP_HEIGHT} pixels")
    
    # 1. Ask the Game Generator for the Spawn Point
    print("Locating Player Spawn...")
    gen = AtlasGenerator(SEED)
    spawn_px_x, spawn_px_y = gen.find_spawn_point()
    
    spawn_tile_x = int(spawn_px_x // TILE_SIZE)
    spawn_tile_y = int(spawn_px_y // TILE_SIZE)
    
    print(f"Player Spawn: ({spawn_tile_x}, {spawn_tile_y})")
    
    # 2. Center the Camera on Spawn
    start_x_offset = spawn_tile_x - (MAP_WIDTH // 2)
    start_y_offset = spawn_tile_y - (MAP_HEIGHT // 2)
    
    t0 = time.time()
    
    # Prepare Shared Memory
    total_bytes = MAP_WIDTH * MAP_HEIGHT * 3
    shm = shared_memory.SharedMemory(create=True, size=total_bytes)
    shape = (MAP_WIDTH, MAP_HEIGHT, 3)
    
    try:
        rows = (MAP_HEIGHT + CHUNK_BATCH - 1) // CHUNK_BATCH
        tasks = [(r, shm.name, shape, SEED, start_x_offset, start_y_offset) for r in range(rows)]
        
        cpu_count = multiprocessing.cpu_count()
        print(f"Rendering with {cpu_count} cores...")
        
        with multiprocessing.Pool(processes=cpu_count) as pool:
            for i, _ in enumerate(pool.imap_unordered(worker_task, tasks)):
                if i % 10 == 0: # Print progress every 10 chunks
                    prog = (i / rows) * 100
                    sys.stdout.write(f"\rProgress: {prog:.1f}%")
        
        print("\nSaving Image...")
        
        # 3. Create Output Directory
        snapshots_dir = os.path.join(current_script_dir, "snapshots")
        os.makedirs(snapshots_dir, exist_ok=True)

        # 4. Save Image with TIMESTAMP
        buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
        surface = pygame.surfarray.make_surface(buffer)
        
        # Draw Spawn Marker (Red Cross)
        center_x = MAP_WIDTH // 2
        center_y = MAP_HEIGHT // 2
        pygame.draw.line(surface, (255, 0, 0), (center_x - 50, center_y), (center_x + 50, center_y), 5)
        pygame.draw.line(surface, (255, 0, 0), (center_x, center_y - 50), (center_x, center_y + 50), 5)
        
        # --- NEW FILENAME LOGIC ---
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(snapshots_dir, f"map_{SEED}_{MAP_WIDTH}x{MAP_HEIGHT}_{timestamp}.png")
        
        pygame.image.save(surface, filename)
        
        print(f"--- ✅ SNAPSHOT SAVED: {filename} ---")
        print(f"Time taken: {time.time() - t0:.2f}s")
        
    finally:
        shm.close()
        shm.unlink()