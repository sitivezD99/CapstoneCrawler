# src/map-snapshots/generate_map_image.py
import os

# --- 🔇 SILENCE PYGAME ---
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import sys
import time
import datetime
import numpy as np
import multiprocessing
import noise

# --- PROFESSIONAL LIBRARIES ---
import cv2 
from tqdm import tqdm 

# --- PATH SETUP ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Navigate up two levels: src/map-snapshots/ -> src/
src_dir = os.path.dirname(os.path.dirname(current_script_dir))
sys.path.append(src_dir)

# --- IMPORT GAME LOGIC ---
try:
    from settings import *
    from world.generator import AtlasGenerator
except ImportError:
    sys.path.append(os.path.dirname(current_script_dir))
    from settings import *
    from world.generator import AtlasGenerator

# --- CONFIGURATION (IN TILES) ---
# We want the map to represent Tiles, where 1 Pixel on the image = 1 Tile in the game.
# 4000 Tiles = 64,000 Game Pixels wide.
MAP_WIDTH_TILES = 30000 
MAP_HEIGHT_TILES = 30000
IMAGE_TILE_SIZE = 1000 # Process 1000x1000 chunks at a time

def generate_tile_task(args):
    """
    Generates a SINGLE 1000x1000 biome grid (represented as 1 pixel per tile).
    """
    file_x_idx, file_y_idx, world_start_tile_x, world_start_tile_y, seed, output_folder = args

    generator = AtlasGenerator(seed)

    # 1. Calculate Grid Coordinates (In Tiles)
    current_tile_x = world_start_tile_x + (file_x_idx * IMAGE_TILE_SIZE)
    current_tile_y = world_start_tile_y + (file_y_idx * IMAGE_TILE_SIZE)

    # 2. Setup Palette (BGR)
    fast_palette = np.zeros((256, 3), dtype=np.uint8)
    for k, v in BIOME_COLORS.items():
        r, g, b = v
        fast_palette[k] = [b, g, r] 

    # 3. Generate Grid (Input is Tile Coordinates)
    try:
        # Note: We pass IMAGE_TILE_SIZE as width/height (1000 tiles)
        biome_indices = generator.generate_grid(current_tile_x, current_tile_y, IMAGE_TILE_SIZE, IMAGE_TILE_SIZE)
        
        # 4. Color Mapping
        tile_image = fast_palette[biome_indices]

        # 5. Save
        filename = os.path.join(output_folder, f"tile_{file_x_idx}_{file_y_idx}.png")
        cv2.imwrite(filename, tile_image)
        return filename
    except Exception as e:
        return f"ERROR: {e}"

def stitch_world_fast(run_folder, cols, rows, spawn_tile_relative=None):
    print(f"\n--- 🧵 STITCHING PREVIEW ---")
    
    final_w = MAP_WIDTH_TILES
    final_h = MAP_HEIGHT_TILES
    
    full_map = np.zeros((final_h, final_w, 3), dtype=np.uint8)
    
    print(f"Image Size: {final_w}x{final_h} pixels (representing {final_w}x{final_h} Tiles)")

    for y in tqdm(range(rows), desc="Stitching"):
        for x in range(cols):
            tile_path = os.path.join(run_folder, f"tile_{x}_{y}.png")
            if not os.path.exists(tile_path): continue
            
            tile = cv2.imread(tile_path)
            if tile is None: continue
            
            # Direct injection
            y1 = y * IMAGE_TILE_SIZE
            y2 = y1 + IMAGE_TILE_SIZE
            x1 = x * IMAGE_TILE_SIZE
            x2 = x1 + IMAGE_TILE_SIZE
            
            # Safety clip in case math is off by 1 pixel
            h, w = tile.shape[:2]
            full_map[y1:y1+h, x1:x1+w] = tile

    # --- MARK SPAWN ---
    if spawn_tile_relative:
        sx, sy = spawn_tile_relative
        # Coordinates are already in Tiles (Pixels on this image)
        img_x, img_y = int(sx), int(sy)
        
        print(f"📍 Marking Spawn at Image Coords: {img_x}, {img_y}")
        color = (0, 0, 255) # Red
        cv2.circle(full_map, (img_x, img_y), 20, color, 2)
        cv2.line(full_map, (img_x - 30, img_y), (img_x + 30, img_y), color, 2)
        cv2.line(full_map, (img_x, img_y - 30), (img_x, img_y + 30), color, 2)
        cv2.putText(full_map, "SPAWN", (img_x + 10, img_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    save_path = os.path.join(run_folder, "FULL_WORLD_PREVIEW.png")
    cv2.imwrite(save_path, full_map)
    print(f"--- ✅ SAVED: {save_path} ---")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    print(f"--- ⚡ MAP GENERATOR v4.0 (Unit Fixed) ---")
    
    gen = AtlasGenerator(SEED)
    
    # 1. Get Spawn in PIXELS (Game Units)
    print("📍 Locating Spawn Point...")
    spawn_px_x, spawn_px_y = gen.find_spawn_point()
    
    # 2. Convert to TILES (Generator Units)
    spawn_tile_x = spawn_px_x / TILE_SIZE
    spawn_tile_y = spawn_px_y / TILE_SIZE
    print(f"   -> Game Pixels: {spawn_px_x}, {spawn_px_y}")
    print(f"   -> Map Tiles:   {int(spawn_tile_x)}, {int(spawn_tile_y)}")
    
    # 3. Center Map on Spawn (In Tile Space)
    half_w = MAP_WIDTH_TILES // 2
    half_h = MAP_HEIGHT_TILES // 2
    
    world_start_tile_x = int(spawn_tile_x - half_w)
    world_start_tile_y = int(spawn_tile_y - half_h)
    
    # Snap to grid chunks for cleanliness
    world_start_tile_x = (world_start_tile_x // IMAGE_TILE_SIZE) * IMAGE_TILE_SIZE
    world_start_tile_y = (world_start_tile_y // IMAGE_TILE_SIZE) * IMAGE_TILE_SIZE
    
    # 4. Prepare Logic
    cols = (MAP_WIDTH_TILES + IMAGE_TILE_SIZE - 1) // IMAGE_TILE_SIZE
    rows = (MAP_HEIGHT_TILES + IMAGE_TILE_SIZE - 1) // IMAGE_TILE_SIZE
    
    snapshots_dir = os.path.join(current_script_dir, "snapshots")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = os.path.join(snapshots_dir, f"run_{timestamp}")
    os.makedirs(run_folder, exist_ok=True)
    
    tasks = []
    for y in range(rows):
        for x in range(cols):
            tasks.append((x, y, world_start_tile_x, world_start_tile_y, SEED, run_folder))

    # 5. Run
    print(f"🚀 Generating {len(tasks)} Tiles...")
    t0 = time.time()
    with multiprocessing.Pool() as pool:
        list(tqdm(pool.imap_unordered(generate_tile_task, tasks), total=len(tasks)))

    # 6. Stitch with Relative Marker
    rel_x = spawn_tile_x - world_start_tile_x
    rel_y = spawn_tile_y - world_start_tile_y
    
    stitch_world_fast(run_folder, cols, rows, spawn_tile_relative=(rel_x, rel_y))
    print(f"--- 🏁 TOTAL TIME: {(time.time() - t0):.2f}s ---")