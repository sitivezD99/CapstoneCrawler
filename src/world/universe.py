# src/world/universe.py
import pygame
import random
from settings import *
from world.world import WorldChunk
from world.generator import AtlasGenerator
from world.cave_generator import CaveGenerator
from world.portal import Portal

class UniverseManager:
    """
    Manages the Multiverse (Surface + Caves) and the Portals between them.
    """
    def __init__(self):
        # Layer 0: Surface
        self.surface_generator = AtlasGenerator(SEED)
        self.surface_chunks = {}
        
        # Layer -1: Underworld
        self.cave_generator = CaveGenerator(SEED)
        self.cave_chunks = {}
        
        # Portals
        self.portals = []
        # Optimization: A quick lookup set for collision logic
        self.portal_locations = set() 
        
        # State
        self.current_layer = 0 # 0 = Surface, -1 = Cave
        
    @property
    def current_chunks(self):
        return self.surface_chunks if self.current_layer == 0 else self.cave_chunks

    def get_chunk(self, cx, cy):
        chunks = self.current_chunks
        
        if (cx, cy) not in chunks:
            # 1. Generate Data
            if self.current_layer == 0:
                grid = self.surface_generator.generate_chunk(cx, cy)
                self._scan_for_portals(cx, cy, grid)
            else:
                grid = self.cave_generator.generate_chunk(cx, cy)
                
            chunks[(cx, cy)] = WorldChunk(cx, cy, grid)
            
        return chunks[(cx, cy)]

    def _scan_for_portals(self, cx, cy, grid):
        """Scans for Cliff Edges to place portals."""
        random.seed(f"{SEED}_{cx}_{cy}_portal")
        if random.random() > 0.3: return

        for y in range(1, CHUNK_SIZE - 1):
            for x in range(1, CHUNK_SIZE - 1):
                tile = grid[x][y]
                
                if tile == BIOME_MTN_LOW:
                    neighbors = [grid[x+1][y], grid[x-1][y], grid[x][y+1], grid[x][y-1]]
                    has_nature = (BIOME_GRASS in neighbors) or (BIOME_FOREST in neighbors)
                    
                    if has_nature:
                        # 100% Chance for testing (As you requested)
                        if random.random() < 1.0: 
                            px = (cx * CHUNK_SIZE + x) * TILE_SIZE
                            py = (cy * CHUNK_SIZE + y) * TILE_SIZE
                            
                            # Add Portal Entity
                            self.portals.append(Portal(px, py))
                            # Add to Fast Lookup Set (for collision logic)
                            self.portal_locations.add((px, py))
                            print(f"🚪 Portal Spawned at {px}, {py}")
                            return 

    def check_portals(self, player):
        """Checks if player is standing on a portal."""
        if self.current_layer != 0: return

        for portal in self.portals:
            # Note: Now that collision is disabled for portals, 
            # the player can walk INSIDE. colliderect will work perfectly.
            if player.rect.colliderect(portal.rect):
                self.teleport_player(player, portal)
                return

    def teleport_player(self, player, portal):
        print("🌀 Teleporting to Underworld...")
        self.current_layer = -1 
        
        landing_x = portal.rect.x
        landing_y = portal.rect.y
        
        # SAFETY CARVE: Ensure landing spot is walkable
        cx = int(landing_x // (CHUNK_SIZE * TILE_SIZE))
        cy = int(landing_y // (CHUNK_SIZE * TILE_SIZE))
        
        chunk = self.get_chunk(cx, cy)
        
        lx = int((landing_x % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        ly = int((landing_y % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        
        # Clear a safe zone
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if 0 <= lx+dx < CHUNK_SIZE and 0 <= ly+dy < CHUNK_SIZE:
                    chunk.grid[lx+dx][ly+dy] = BIOME_CAVE_CORRIDOR 
        
        player.rect.x = landing_x
        player.rect.y = landing_y

    def get_nearby_walls(self, player_rect):
        """
        Standard collision check, BUT ignores walls that have Portals.
        This allows the player to walk 'into' the mountain door.
        """
        walls = []
        center_cx = int(player_rect.centerx // (CHUNK_SIZE * TILE_SIZE))
        center_cy = int(player_rect.centery // (CHUNK_SIZE * TILE_SIZE))
        
        for cy in range(center_cy - 1, center_cy + 2):
            for cx in range(center_cx - 1, center_cx + 2):
                chunk = self.get_chunk(cx, cy)
                for r in range(CHUNK_SIZE):
                    for c in range(CHUNK_SIZE):
                        tile_id = chunk.grid[r][c] 
                        if tile_id in COLLISION_TILES:
                            px = (cx * CHUNK_SIZE + r) * TILE_SIZE
                            py = (cy * CHUNK_SIZE + c) * TILE_SIZE
                            
                            # --- CRITICAL FIX ---
                            # If this wall is actually a Portal, DO NOT treat it as a wall.
                            if (px, py) in self.portal_locations:
                                continue
                                
                            walls.append(pygame.Rect(px, py, TILE_SIZE, TILE_SIZE))
        return walls

    def draw_visible_chunks(self, screen, camera):
        cam_x = -camera.camera.x
        cam_y = -camera.camera.y
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        chunk_px_w = CHUNK_SIZE * TILE_SIZE
        
        start_cx = int(cam_x // chunk_px_w)
        start_cy = int(cam_y // chunk_px_w)
        end_cx = int((cam_x + screen_w) // chunk_px_w) + 1
        end_cy = int((cam_y + screen_h) // chunk_px_w) + 1
        
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                chunk = self.get_chunk(cx, cy)
                chunk_x_offset = cx * chunk_px_w
                chunk_y_offset = cy * chunk_px_w
                
                for x in range(CHUNK_SIZE):
                    for y in range(CHUNK_SIZE):
                        tile_id = chunk.grid[x][y]
                        if tile_id == BIOME_DEEP_OCEAN: continue 

                        dest_x = chunk_x_offset + (x * TILE_SIZE) + camera.camera.x
                        dest_y = chunk_y_offset + (y * TILE_SIZE) + camera.camera.y
                        
                        if -TILE_SIZE <= dest_x < screen_w and -TILE_SIZE <= dest_y < screen_h:
                            color = BIOME_COLORS.get(tile_id, (255, 0, 255))
                            pygame.draw.rect(screen, color, (dest_x, dest_y, TILE_SIZE, TILE_SIZE))
                            
        if self.current_layer == 0:
            for portal in self.portals:
                portal.draw(screen, camera)
    
    def toggle_layer(self):
        if self.current_layer == 0: self.current_layer = -1
        else: self.current_layer = 0