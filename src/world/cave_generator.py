# src/world/cave_generator.py
import random
import math
import noise
import numpy as np
from settings import *

class CaveGenerator:
    """
    PROFESSIONAL CAVE GENERATOR (Final Polish)
    - Generates huge (but reasonable) rooms.
    - Connects them with organic, fluid corridors.
    - Optimized for infinite generation without artifacts.
    """
    def __init__(self, seed):
        self.seed = seed
        
        # --- 1. THE SKELETON (Macro Grid) ---
        # Determines how spread out the rooms are.
        # 60 tiles = A good balance between "Open" and "Navigable".
        self.macro_grid_size = 70 
        self.room_chance = 0.65      # 65% chance a sector has a room
        
        # --- 2. THE BODY (Sizes) ---
        # Rooms are now screen-sized arenas, not continent-sized voids.
        self.min_room_radius = 15     # ~16 tiles wide
        self.max_room_radius = 30    # ~40 tiles wide
        self.corridor_width = 10      # ~8 tiles wide (Walkable but tight enough to be a tunnel)
        
        # --- 3. THE SOUL (Organic Warping) ---
        # We distort coordinates to make shapes look natural.
        # Reduced strength prevents corridors from "tearing" or looping weirdly.
        self.warp_strength = 15.0    
        self.warp_frequency = 0.02   

    def get_pseudo_random(self, x, y, salt=""):
        """Deterministic random number generator."""
        random.seed(f"{self.seed}_{x}_{y}_{salt}")
        return random.random()

    def _get_warp(self, x, y):
        """
        Distorts the coordinate system.
        Turns perfect circles/lines into natural blobs/snakes.
        """
        # Perlin noise offsets the "camera" position
        dx = noise.snoise2(x * self.warp_frequency, y * self.warp_frequency, base=self.seed)
        dy = noise.snoise2(x * self.warp_frequency, y * self.warp_frequency, base=self.seed + 999)
        
        return x + (dx * self.warp_strength), y + (dy * self.warp_strength)

    def get_room_info(self, mx, my):
        """
        Calculates the Blueprint for a room in sector (mx, my).
        Returns dict or None.
        """
        # 1. Check Existence
        if self.get_pseudo_random(mx, my, "exists") > self.room_chance:
            return None 
        
        # 2. Calculate Position (Jittered inside the cell)
        padding = self.max_room_radius + 4
        cell_w = self.macro_grid_size
        
        # Safe-guard: If cell is too small for the room, center it.
        if (cell_w - 2 * padding) <= 0:
            local_x = cell_w / 2
            local_y = cell_w / 2
        else:
            local_x = padding + self.get_pseudo_random(mx, my, "x") * (cell_w - 2 * padding)
            local_y = padding + self.get_pseudo_random(mx, my, "y") * (cell_w - 2 * padding)
        
        global_x = (mx * cell_w) + local_x
        global_y = (my * cell_w) + local_y
        
        # 3. Calculate Radius
        t = self.get_pseudo_random(mx, my, "size")
        radius = self.min_room_radius + t * (self.max_room_radius - self.min_room_radius)
        
        return {'center': (global_x, global_y), 'radius': radius}

    def generate_chunk(self, cx, cy):
        """
        Generates a 32x32 chunk of the cave system.
        """
        # Start with Solid Wall
        chunk_grid = np.full((CHUNK_SIZE, CHUNK_SIZE), BIOME_CAVE_WALL, dtype=np.int32)
        
        chunk_world_x = cx * CHUNK_SIZE
        chunk_world_y = cy * CHUNK_SIZE
        
        # --- STEP 1: GATHER BLUEPRINTS ---
        # Scan a 3x3 area of Macro Sectors to find relevant rooms/halls
        start_mx = int((chunk_world_x - self.macro_grid_size) // self.macro_grid_size)
        start_my = int((chunk_world_y - self.macro_grid_size) // self.macro_grid_size)
        
        rooms = []
        corridors = []

        for my in range(start_my, start_my + 3):
            for mx in range(start_mx, start_mx + 3):
                room = self.get_room_info(mx, my)
                if room:
                    rooms.append(room)
                    
                    # Connect to Neighbors (Right and Down) to form the graph
                    neighbors = [(mx + 1, my), (mx, my + 1)]
                    for nx, ny in neighbors:
                        neighbor_room = self.get_room_info(nx, ny)
                        if neighbor_room:
                            corridors.append((room['center'], neighbor_room['center']))

        # --- STEP 2: RASTERIZE (Draw the Map) ---
        for y in range(CHUNK_SIZE):
            for x in range(CHUNK_SIZE):
                real_x = chunk_world_x + x
                real_y = chunk_world_y + y
                
                # A. Apply Fluid Warping (The Naturalizer)
                # We check the shape at the DISTORTED coordinate
                wx, wy = self._get_warp(real_x, real_y)
                
                # B. Draw Rooms
                in_room = False
                for room in rooms:
                    rx, ry = room['center'] 
                    # Distance from Warped Point to Real Room Center
                    dist = math.hypot(wx - rx, wy - ry)
                    
                    if dist <= room['radius']:
                        chunk_grid[x][y] = BIOME_CAVE_ROOM
                        in_room = True
                        break
                
                if in_room: continue

                # C. Draw Corridors
                for p1, p2 in corridors:
                    # Distance from Warped Point to Straight Line
                    dist = self._point_to_segment_dist(wx, wy, p1, p2)
                    
                    # Add subtle "breathing" to corridor width so it's not a pipe
                    swell = noise.snoise2(real_x * 0.04, real_y * 0.04, base=self.seed + 500) * 2.0
                    effective_width = self.corridor_width + swell
                    
                    if dist <= (effective_width / 2):
                        chunk_grid[x][y] = BIOME_CAVE_CORRIDOR
                        break

        return chunk_grid

    def _point_to_segment_dist(self, px, py, p1, p2):
        """Math helper: Shortest distance from point to line segment."""
        x1, y1 = p1
        x2, y2 = p2
        dx, dy = x2 - x1, y2 - y1
        
        if dx == 0 and dy == 0: 
            return math.hypot(px - x1, py - y1)
            
        t = ((px - x1) * dx + (py - y1) * dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t)) # Clamp to segment
        
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return math.hypot(px - closest_x, py - closest_y)