# src/settings.py

# Screen & Rendering
WIDTH = 1280
HEIGHT = 720
FPS = 60
TILE_SIZE = 32
CHUNK_SIZE = 32  # 32x32 tiles per chunk
RENDER_DISTANCE = 4  # Reduced slightly to account for heavier math

# Physics & Player
PLAYER_SPEED = 0.5
PLAYER_FRICTION = 0.85
PLAYER_MAX_SPEED = 6

# ---------------- GENERATION DNA ----------------
SEED = 2026

# STEP A: ROOM NODES (The Skeleton)
# We divide the world into a coarse grid. Each cell might contain a room.
ROOM_GRID_SIZE = 35      # Every 40x40 tiles, try to place a room
ROOM_CHANCE = 0.65        # 70% chance a grid cell has a room
ROOM_MIN_RADIUS = 6      # Smallest room (in tiles)
ROOM_MAX_RADIUS = 18     # Largest room

# STEP B: WORM TUNNELS (The Connectors)
# Ridged Noise settings
TUNNEL_FREQ = 0.03       # Lower = Longer, straighter tunnels
TUNNEL_THICKNESS = 0.14  # Threshold for the "Zero Crossing"

# STEP C: EROSION (The Polish)
# Cellular Automata settings
SMOOTHING_PASSES = 2     # How many times to erode (1 is usually enough)
WALL_THRESHOLD = 5       # If a tile has > 4 wall neighbors, it becomes a wall

# ... (Previous settings) ...

# RPG SETTINGS
ATTACK_DURATION = 0.2    # How long the hit lasts (seconds)
ATTACK_COOLDOWN = 0.4    # Time between hits (seconds)

# STARTING STATS
BASE_STATS = {
    'str': 5,
    'agi': 5,
    'int': 5,
    'vit': 10  # Higher VIT for testing so you don't die instantly
}


# We use these to tell the Spawner what is a "Room" and what is a "Tunnel"
TILE_WALL = 0
TILE_CAVERN = 1  # Safe for Monsters
TILE_TUNNEL = 2  # No Monsters allowed