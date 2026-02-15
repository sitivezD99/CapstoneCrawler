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

# --- NOISE SETTINGS ---
# SCALE: Controls the "Zoom".
# 0.002 Matches your 'Ultra' map generator code.
SCALE = 0.0015        

OCTAVES = 5           
PERSISTENCE = 0.45     
LACUNARITY = 2.0      

# --- THRESHOLDS (Synced with generate_map.py) ---
# These match the logic in the worker_task function
SEA_LEVEL = 0.20        
BEACH_LEVEL = 0.25     # Land starts here
GRASS_LEVEL = 0.35    
FOREST_LEVEL = 0.55   

# --- MOUNTAIN LAYERS ---
MTN_LOW_LEVEL = 0.70   
MTN_MID_LEVEL = 0.85   
MTN_HIGH_LEVEL = 1.00  

# --- BIOME IDs ---
BIOME_DEEP_OCEAN = 0
BIOME_OCEAN = 1
BIOME_BEACH = 2
BIOME_GRASS = 3
BIOME_FOREST = 4
BIOME_MTN_LOW = 5      
BIOME_MTN_MID = 6     
BIOME_MTN_HIGH = 7     

# --- BIOME COLORS ---
BIOME_COLORS = {
    BIOME_DEEP_OCEAN: (10, 10, 50),       
    BIOME_OCEAN:      (20, 60, 200),    
    BIOME_BEACH:      (240, 240, 60),  
    BIOME_GRASS:      (50, 200, 50),    
    BIOME_FOREST:     (10, 120, 10),      
    BIOME_MTN_LOW:    (100, 100, 100),  
    BIOME_MTN_MID:    (150, 150, 150),  
    BIOME_MTN_HIGH:   (255, 255, 255)   
}

# --- COLLISION RULES ---
COLLISION_TILES = {BIOME_DEEP_OCEAN, BIOME_MTN_HIGH, BIOME_MTN_MID}

# --- RPG COMBAT SETTINGS ---
ATTACK_DURATION = 0.2
ATTACK_COOLDOWN = 0.4
BASE_STATS = {'str': 5, 'agi': 5, 'int': 5, 'vit': 10}