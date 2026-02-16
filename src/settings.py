# src/settings.py
import pygame

# --- SCREEN & RENDERING ---
WIDTH = 1280
HEIGHT = 720
FPS = 60
TILE_SIZE = 16
CHUNK_SIZE = 32
RENDER_DISTANCE = 5

# --- PHYSICS ---
PLAYER_SPEED = 0.5
PLAYER_FRICTION = 0.85
PLAYER_MAX_SPEED = 6

# --- SHATTERED ATLAS GENERATION DNA ---
SEED = 2026

# --- "AAA" SCALE SETTINGS ---
CONTINENT_SCALE = 0.00015  
DETAIL_SCALE = 0.003      
WARP_STRENGTH = 150.0
OCTAVES = 6           
PERSISTENCE = 0.5     
LACUNARITY = 2.0      

# --- GENERATION THRESHOLDS (SINGLE SOURCE OF TRUTH) ---
# This ensures the Spawner and the Map Generator agree on what is "Land"
LAND_THRESHOLD = 0.12 

# --- BIOME IDs ---
BIOME_DEEP_OCEAN = 0
BIOME_OCEAN = 1         # The "Mid" Water
BIOME_SHALLOW_WATER = 8 # Walkable Water
BIOME_BEACH = 2
BIOME_GRASS = 3
BIOME_FOREST = 4
BIOME_MTN_LOW = 5      
BIOME_MTN_MID = 6     
BIOME_MTN_HIGH = 7    

# --- UNDERWORLD BIOME IDs ---
BIOME_CAVE_WALL = 100
BIOME_CAVE_ROOM = 101      # The "Open Caverns"
BIOME_CAVE_CORRIDOR = 102  # The "Connecting Arteries"

# --- BIOME COLORS ---
BIOME_COLORS = {
    # Surface
    BIOME_DEEP_OCEAN:    (5, 5, 30),       
    BIOME_OCEAN:         (20, 40, 90),    
    BIOME_SHALLOW_WATER: (60, 160, 200),
    BIOME_BEACH:         (240, 240, 100),  
    BIOME_GRASS:         (50, 200, 50),    
    BIOME_FOREST:        (10, 100, 10),      
    BIOME_MTN_LOW:       (90, 90, 90),  
    BIOME_MTN_MID:       (140, 140, 140),  
    BIOME_MTN_HIGH:      (255, 255, 255),
    
    # CAVE COLORS (Clean, distinct colors)
    BIOME_CAVE_WALL:     (10, 10, 15),     # Pitch Black
    BIOME_CAVE_ROOM:     (60, 60, 80),     # Dark Blue-Grey (The Massive Rooms)
    BIOME_CAVE_CORRIDOR: (100, 90, 80)     # Lighter Brown-Grey (The Connecting Paths)
}

# --- COLLISION RULES ---
# Tiles the player CANNOT walk on
COLLISION_TILES = {BIOME_DEEP_OCEAN, BIOME_OCEAN, BIOME_MTN_LOW, BIOME_MTN_MID, BIOME_MTN_HIGH}
# Add Cave Walls to collision
COLLISION_TILES.add(BIOME_CAVE_WALL)

# --- RPG COMBAT SETTINGS ---
ATTACK_DURATION = 0.2
ATTACK_COOLDOWN = 0.4
BASE_STATS = {'str': 5, 'agi': 5, 'int': 5, 'vit': 10}

# --- CAVE CONFIGURATION (PROFESSIONAL SCALE) ---
# These control the "Composite Noise" generator
CAVE_SCALE_ROOMS = 0.015      # Low number = MASSIVE Rooms
CAVE_SCALE_CORRIDORS = 0.02   # Scale for the tunnel network
CAVE_CORRIDOR_WIDTH = 0.18    # Thickness of corridors (High = Wider)
CAVE_ROOM_THRESHOLD = 0.4     # How "open" the rooms are
CAVE_WARP_STRENGTH = 15.0     # How jagged the walls are


# --- PORTAL SETTINGS ---
PORTAL_CHANCE = 1.00    # 5% chance a valid cliff gets a portal (Keeps them rare)
PORTAL_COLOR = (0, 0, 0) # Pure Black Hole