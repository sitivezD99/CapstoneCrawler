# Screen & Rendering
WIDTH = 1280
HEIGHT = 720
FPS = 60
TILE_SIZE = 32
CHUNK_SIZE = 32  # 16x16 tiles per chunk
RENDER_DISTANCE = 6  # How many chunks away to draw

# Physics & Player
PLAYER_SPEED = 0.5        # Acceleration
PLAYER_FRICTION = 0.85    # Slippery-ness (0.9 = Ice, 0.5 = Mud)
PLAYER_MAX_SPEED = 6

# ---------------- THE NOISE MATH ----------------
# SEED: Change this to generate a completely new world
SEED = 8141999 #14081999

# LAYER A: The "Big Caverns" (Open Spaces)
# Low frequency = Massive features. High threshold = Rarer caves.
CAVE_FREQ = 0.033333333333333333  
CAVE_THRESHOLD = 0.33333333333333333333

# LAYER B: The "Worm Tunnels" (Twisting Corridors)
# Ridged Noise: We take the absolute value close to zero.
# Higher frequency = Tighter, windier tunnels.
TUNNEL_FREQ = 0.01
TUNNEL_WIDTH = 0.04 # How thick the tunnels are