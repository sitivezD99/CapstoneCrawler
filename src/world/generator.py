import opensimplex
from settings import *

class TerrainGenerator:
    def __init__(self, seed):
        self.seed = seed
        self.noise_gen = opensimplex.OpenSimplex(seed)

    def get_tile_at(self, x, y):
        """
        Determines if a specific global coordinate is a WALL or FLOOR.
        Returns: 1 for Floor, 0 for Wall
        """
        
        # 1. LAYER A: Big Organic Caverns (Standard Noise)
        # We sample the noise at the coordinates. 
        base_noise = self.noise_gen.noise2(x * CAVE_FREQ, y * CAVE_FREQ)
        is_cavern = base_noise > CAVE_THRESHOLD

        # 2. LAYER B: Twisting Tunnels (Ridged Noise)
        # We use absolute value to find the "zero crossing" lines.
        # This creates long, winding paths.
        tunnel_noise = self.noise_gen.noise2(x * TUNNEL_FREQ, y * TUNNEL_FREQ)
        is_tunnel = abs(tunnel_noise) < TUNNEL_WIDTH

        # 3. COMBINATION
        # If it's a cavern OR a tunnel, it's walkable floor.
        if is_cavern or is_tunnel:
            return 1 # Floor
        else:
            return 0 # Wall