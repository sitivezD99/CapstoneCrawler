# src/world/universe.py
import pygame
import random
import math
import noise 
from settings import *
from world.world import WorldChunk
from world.generator import AtlasGenerator
from world.cave_generator import CaveGenerator
from world.portal import Portal

class UniverseManager:
    """
    The 'Aggressive' Universe Manager.
    - Surface Portals spawn based on PORTAL_CHANCE.
    - Cave Natural Exits spawn based on PORTAL_CHANCE (Fixed!).
    - Guaranteed Bi-Directional consistency.
    """
    def __init__(self):
        # Layer 0: Surface
        self.surface_generator = AtlasGenerator(SEED)
        self.surface_chunks = {}
        self.surface_portals = [] 
        
        # Layer -1: Underworld
        self.cave_generator = CaveGenerator(SEED)
        self.cave_chunks = {}
        self.cave_portals = []    
        
        # State
        self.current_layer = 0 
        self.last_teleport_time = 0
        self.teleport_cooldown = 1200 
        
    @property
    def current_chunks(self):
        return self.surface_chunks if self.current_layer == 0 else self.cave_chunks

    @property
    def active_portals(self):
        return self.surface_portals if self.current_layer == 0 else self.cave_portals

    def get_chunk(self, cx, cy):
        chunks = self.current_chunks
        
        if (cx, cy) not in chunks:
            if self.current_layer == 0:
                grid = self.surface_generator.generate_chunk(cx, cy)
                self._scan_for_surface_portals(cx, cy, grid)
            else:
                grid = self.cave_generator.generate_chunk(cx, cy)
                self._scan_for_cave_portals(cx, cy, grid)
                
            chunks[(cx, cy)] = WorldChunk(cx, cy, grid)
            
        return chunks[(cx, cy)]

    def _scan_for_surface_portals(self, cx, cy, grid):
        """Places portals on Surface Cliffs."""
        random.seed(f"{SEED}_{cx}_{cy}_portal_down")
        valid_ground = [BIOME_GRASS, BIOME_FOREST, BIOME_BEACH]
        neighbor_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for y in range(1, CHUNK_SIZE - 1):
            for x in range(1, CHUNK_SIZE - 1):
                if grid[x][y] in [BIOME_MTN_LOW, BIOME_MTN_MID]:
                    for dx, dy in neighbor_offsets:
                        if grid[x+dx][y+dy] in valid_ground:
                            if random.random() < PORTAL_CHANCE:
                                px = (cx * CHUNK_SIZE + (x + dx)) * TILE_SIZE
                                py = (cy * CHUNK_SIZE + (y + dy)) * TILE_SIZE
                                
                                self.surface_portals.append(Portal(px, py, -1))
                                print(f"🚪 Surface Portal Spawned at {px}, {py}")
                                return 

    def _scan_for_cave_portals(self, cx, cy, grid):
        """
        Places natural exits in Cave Rooms.
        FIX: Now obeys PORTAL_CHANCE and scans aggressively for valid rooms.
        """
        random.seed(f"{SEED}_{cx}_{cy}_portal_up")
        
        # 1. Obey the Global Chance Setting (User Control)
        if random.random() > PORTAL_CHANCE: 
            return

        # 2. Scan the Chunk for a Valid Room Tile
        # We ignore the very edges to avoid clipping
        margin = 4
        for y in range(margin, CHUNK_SIZE - margin, 2): # Step 2 optimization
            for x in range(margin, CHUNK_SIZE - margin, 2):
                
                if grid[x][y] == BIOME_CAVE_ROOM:
                    px = (cx * CHUNK_SIZE + x) * TILE_SIZE
                    py = (cy * CHUNK_SIZE + y) * TILE_SIZE
                    
                    # 3. Periscope Check: Ensure we don't exit into Ocean
                    if self._periscope_check_surface_land(px, py):
                        self.cave_portals.append(Portal(px, py, 0))
                        print(f"🪜 Natural Cave Exit Spawned at {px}, {py}")
                        return # Limit 1 exit per chunk

    def _periscope_check_surface_land(self, world_x, world_y):
        """Math-only check to see if surface is land."""
        gen_scale = 0.00015 
        nx = (world_x / TILE_SIZE) * gen_scale
        ny = (world_y / TILE_SIZE) * gen_scale
        
        n = noise.snoise2(nx, ny, octaves=6, persistence=0.5, lacunarity=2.0, base=SEED)
        h = n * n * n * 4.0
        
        return h > (LAND_THRESHOLD + 0.05)

    def check_portals(self, player):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_teleport_time < self.teleport_cooldown:
            return 

        for portal in self.active_portals:
            if player.rect.colliderect(portal.rect):
                self.teleport_player(player, portal)
                return

    def teleport_player(self, player, portal):
        self.last_teleport_time = pygame.time.get_ticks()
        origin_x, origin_y = portal.rect.x, portal.rect.y
        target_layer = portal.target_layer
        
        print(f"🌀 Teleporting to Layer {target_layer}...")
        
        # --- PHASE 1: DETERMINE DESTINATION ---
        dest_x, dest_y = 0, 0
        
        if portal.linked_pos:
            dest_x, dest_y = portal.linked_pos
        else:
            if target_layer == -1:
                # Down -> Find nearest Cave Floor (Or force one)
                dest_x, dest_y = self._find_nearest_cave_floor(origin_x, origin_y)
            else:
                # Up -> Surface is Land
                dest_x, dest_y = origin_x, origin_y
                
            portal.linked_pos = (dest_x, dest_y)

            # Create Bi-Directional Link
            if target_layer == -1:
                self.current_layer = -1 
                ret_portal = Portal(dest_x, dest_y, 0)
                ret_portal.linked_pos = (origin_x, origin_y)
                self.cave_portals.append(ret_portal)
                self.current_layer = 0
            else:
                self.current_layer = 0
                ret_portal = Portal(dest_x, dest_y, -1)
                ret_portal.linked_pos = (origin_x, origin_y)
                self.surface_portals.append(ret_portal)
                self.current_layer = -1 

        # --- PHASE 2: SWITCH LAYERS ---
        self.current_layer = target_layer
        
        # --- PHASE 3: FIND SAFE SPAWN NEIGHBOR ---
        spawn_x, spawn_y = self._find_best_spawn_neighbor(dest_x, dest_y)
        
        player.rect.x = spawn_x
        player.rect.y = spawn_y
        print(f"✨ Arrived safely at {spawn_x}, {spawn_y}")

    def _find_best_spawn_neighbor(self, target_x, target_y):
        candidates = []
        offsets = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for ox, oy in offsets:
            check_x = target_x + (ox * TILE_SIZE)
            check_y = target_y + (oy * TILE_SIZE)
            
            if self._is_walkable(check_x, check_y):
                score = self._calculate_openness_score(check_x, check_y)
                candidates.append({'pos': (check_x, check_y), 'score': score})
        
        if not candidates:
            # Fallback: Force safety
            self._force_tile_safety(target_x, target_y + TILE_SIZE)
            return target_x, target_y + TILE_SIZE
        
        candidates.sort(key=lambda c: c['score'], reverse=True)
        return candidates[0]['pos']

    def _calculate_openness_score(self, world_x, world_y):
        score = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0: continue
                if self._is_walkable(world_x + dx*TILE_SIZE, world_y + dy*TILE_SIZE):
                    score += 1
        return score

    def _is_walkable(self, world_x, world_y):
        cx = int(world_x // (CHUNK_SIZE * TILE_SIZE))
        cy = int(world_y // (CHUNK_SIZE * TILE_SIZE))
        chunk = self.get_chunk(cx, cy)
        lx = int((world_x % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        ly = int((world_y % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        
        if 0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE:
            tile = chunk.grid[lx][ly]
            valid_tiles = [BIOME_GRASS, BIOME_BEACH, BIOME_FOREST, 
                           BIOME_CAVE_ROOM, BIOME_CAVE_CORRIDOR]
            return tile in valid_tiles
        return False

    def _find_nearest_cave_floor(self, start_x, start_y):
        center_tx = int(start_x // TILE_SIZE)
        center_ty = int(start_y // TILE_SIZE)
        search_radius = 200 
        
        if self._is_cave_safe_check(center_tx, center_ty):
            return (center_tx * TILE_SIZE, center_ty * TILE_SIZE)

        x, y = 0, 0
        dx, dy = 0, -1
        for i in range(search_radius**2):
            check_x, check_y = center_tx + x, center_ty + y
            if self._is_cave_safe_check(check_x, check_y):
                return (check_x * TILE_SIZE, check_y * TILE_SIZE)
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1-y):
                dx, dy = -dy, dx
            x, y = x+dx, y+dy
        
        # Force room
        self._force_tile_safety(start_x, start_y + TILE_SIZE)
        return (start_x, start_y) 

    def _is_cave_safe_check(self, tx, ty):
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        lx = tx % CHUNK_SIZE
        ly = ty % CHUNK_SIZE
        if (cx, cy) in self.cave_chunks:
            chunk = self.cave_chunks[(cx, cy)]
        else:
            grid = self.cave_generator.generate_chunk(cx, cy)
            self.cave_chunks[(cx, cy)] = WorldChunk(cx, cy, grid)
            chunk = self.cave_chunks[(cx, cy)]
        return chunk.grid[lx][ly] in [BIOME_CAVE_ROOM, BIOME_CAVE_CORRIDOR]

    def _force_tile_safety(self, world_x, world_y):
        cx = int(world_x // (CHUNK_SIZE * TILE_SIZE))
        cy = int(world_y // (CHUNK_SIZE * TILE_SIZE))
        lx = int((world_x % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        ly = int((world_y % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        chunk = self.get_chunk(cx, cy)
        chunk.grid[lx][ly] = BIOME_CAVE_CORRIDOR
        chunk.rebuild()

    def get_nearby_walls(self, player_rect):
        walls = []
        center_cx = int(player_rect.centerx // (CHUNK_SIZE * TILE_SIZE))
        center_cy = int(player_rect.centery // (CHUNK_SIZE * TILE_SIZE))
        for cy in range(center_cy - 1, center_cy + 2):
            for cx in range(center_cx - 1, center_cx + 2):
                chunk = self.get_chunk(cx, cy)
                walls.extend(chunk.rects)
        return walls

    def draw_visible_chunks(self, screen, camera):
        cam_x, cam_y = -camera.camera.x, -camera.camera.y
        screen_w, screen_h = screen.get_width(), screen.get_height()
        chunk_px = CHUNK_SIZE * TILE_SIZE
        start_cx = int(cam_x // chunk_px)
        start_cy = int(cam_y // chunk_px)
        end_cx = int((cam_x + screen_w) // chunk_px) + 1
        end_cy = int((cam_y + screen_h) // chunk_px) + 1
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                chunk = self.get_chunk(cx, cy)
                ox, oy = cx * chunk_px, cy * chunk_px
                for x in range(CHUNK_SIZE):
                    for y in range(CHUNK_SIZE):
                        tile = chunk.grid[x][y]
                        if tile == BIOME_DEEP_OCEAN: continue 
                        dx = ox + (x * TILE_SIZE) + camera.camera.x
                        dy = oy + (y * TILE_SIZE) + camera.camera.y
                        if -TILE_SIZE <= dx < screen_w and -TILE_SIZE <= dy < screen_h:
                            color = BIOME_COLORS.get(tile, (255, 0, 255))
                            pygame.draw.rect(screen, color, (dx, dy, TILE_SIZE, TILE_SIZE))
        for portal in self.active_portals:
            portal.draw(screen, camera)
            
    def toggle_layer(self):
        if self.current_layer == 0: self.current_layer = -1
        else: self.current_layer = 0