# src/settings.py
import pygame

# --- SCREEN & RENDERING ---
WIDTH = 1280
HEIGHT = 720
FPS = 60
TILE_SIZE = 16      # 16px Tiles (Vast World)
CHUNK_SIZE = 32     # 32x32 Chunks
RENDER_DISTANCE = 5

# --- PHYSICS ---
PLAYER_SPEED = 0.5
PLAYER_FRICTION = 0.85
PLAYER_MAX_SPEED = 6

# --- GENERATION SETTINGS ---
SEED = 2026
CONTINENT_SCALE = 0.00015  # Your original continent scale
BLOB_SCALE = 0.002         # Size of the Biome Blobs (Lower = Bigger Blobs)
OCTAVES = 6           
PERSISTENCE = 0.5     
LACUNARITY = 2.0
LAND_THRESHOLD = 0.12      

# --- ZONING THRESHOLDS ---
# Below 0.45 = Zone 1 (Lowlands/Coastal)
# Above 0.45 = Zone 2 (Highlands/Inland)
HIGHLAND_THRESHOLD = 0.45 

# --- BIOME IDs ---
# Water
BIOME_DEEP_OCEAN = 0
BIOME_OCEAN = 1       
BIOME_SHALLOW_WATER = 8 
BIOME_BEACH = 2

# ZONE 1: LOWLANDS (Near Water)
BIOME_L_MEADOW = 10     # Standard Green
BIOME_L_SCRUB = 11      # Dry Yellowish
BIOME_L_MARSH = 12      # Dark Teal/Green

# ZONE 2: HIGHLANDS (Inland)
BIOME_H_FOREST = 20     # Deep Green
BIOME_H_AUTUMN = 21     # Orange/Red
BIOME_H_BIRCH = 22      # Pale Green

# Mountains
BIOME_MTN_LOW = 30      
BIOME_MTN_HIGH = 31     
BIOME_MTN_PEAK = 32    

# Caves
BIOME_CAVE_WALL = 200
BIOME_CAVE_ROOM = 201      
BIOME_CAVE_CORRIDOR = 202  

# --- BIOME COLORS (Plain Colors, No Textures) ---
BIOME_COLORS = {
    # Water
    BIOME_DEEP_OCEAN:    (5, 5, 30),       
    BIOME_OCEAN:         (20, 40, 90),    
    BIOME_SHALLOW_WATER: (60, 160, 200),
    BIOME_BEACH:         (240, 240, 100),  
    
    # ZONE 1: Lowland Blobs
    BIOME_L_MEADOW:      (100, 255, 100),  # Bright Neon Green
    BIOME_L_SCRUB:       (200, 200, 100),  # Dull Yellow
    BIOME_L_MARSH:       (50, 150, 150),   # Teal/Swampy
    
    # ZONE 2: Highland Blobs
    BIOME_H_FOREST:      (0, 100, 0),      # Dark Green
    BIOME_H_AUTUMN:      (200, 100, 50),   # Orange
    BIOME_H_BIRCH:       (150, 200, 150),  # Pale Mint
    
    # Mountains
    BIOME_MTN_LOW:       (90, 90, 90),  
    BIOME_MTN_HIGH:      (140, 140, 140),  
    BIOME_MTN_PEAK:      (255, 255, 255),
    
    # Caves
    BIOME_CAVE_WALL:     (10, 10, 15),     
    BIOME_CAVE_ROOM:     (60, 60, 80),     
    BIOME_CAVE_CORRIDOR: (100, 90, 80)     
}

# --- COLLISION RULES ---
# Only Water, Mountains, and Cave Walls block movement now.
# NO TREES, NO ROCKS.
COLLISION_TILES = {
    BIOME_DEEP_OCEAN, BIOME_OCEAN, 
    BIOME_MTN_LOW, BIOME_MTN_HIGH, BIOME_MTN_PEAK,
    BIOME_CAVE_WALL
}

# --- COMBAT ---
ATTACK_DURATION = 0.2
ATTACK_COOLDOWN = 0.4
BASE_STATS = {'str': 5, 'agi': 5, 'int': 5, 'vit': 10}

# --- CAVE CONFIG ---
CAVE_SCALE_ROOMS = 0.015      
CAVE_SCALE_CORRIDORS = 0.02   
CAVE_CORRIDOR_WIDTH = 0.18    
CAVE_ROOM_THRESHOLD = 0.4     
CAVE_WARP_STRENGTH = 15.0     

# --- PORTAL ---
PORTAL_CHANCE = 1.00    
PORTAL_COLOR = (0, 0, 0)