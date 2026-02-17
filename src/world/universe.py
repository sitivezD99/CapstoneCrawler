# src/world/universe.py
import pygame
import random
import math
from settings import *
from world.world import WorldChunk
from world.generator import AtlasGenerator
from world.cave_generator import CaveGenerator
from world.portal import Portal

class UniverseManager:
    """
    The 'Walkable & Cached' Universe Manager.
    - Fix 1: Surface Portals spawn on the WALKABLE Forest tile (Green).
    - Fix 2: Pre-generates and SAVES the cave chunk to ensure 100% link accuracy.
    - Fix 3: Returns Teleport Status to fix Frame-Sync glitches.
    """
    def __init__(self):
        self.surface_generator = AtlasGenerator(SEED) 
        self.cave_generator = CaveGenerator(SEED) 
        self.surface_chunks = {} 
        self.cave_chunks = {} 
        self.surface_portals = [] 
        self.cave_portals = [] 
        self.current_layer = 0 
        self.last_teleport_time = 0 
        self.teleport_cooldown = 1500 

    @property
    def current_chunks(self):
        return self.surface_chunks if self.current_layer == 0 else self.cave_chunks

    @property
    def active_portals(self):
        return self.surface_portals if self.current_layer == 0 else self.cave_portals

    def get_chunk(self, cx, cy):
        chunks = self.current_chunks
        
        if (cx, cy) not in chunks:
            # 1. Generate Grid
            if self.current_layer == 0:
                grid = self.surface_generator.generate_chunk(cx, cy)
                
                # Verify links against cached cave data
                self._ensure_cave_chunk_exists(cx, cy)
                cave_grid = self.cave_chunks[(cx, cy)].grid
                
                valid_links = self._find_verified_portal_links(cx, cy, grid, cave_grid)
                self._instantiate_portals(valid_links)
            else:
                # Load cached or generate new
                if (cx, cy) in self.cave_chunks:
                    grid = self.cave_chunks[(cx, cy)].grid
                else:
                    grid = self.cave_generator.generate_chunk(cx, cy)

            chunk = WorldChunk(cx, cy, grid)
            chunks[(cx, cy)] = chunk
            
        return chunks[(cx, cy)]

    def _ensure_cave_chunk_exists(self, cx, cy):
        if (cx, cy) not in self.cave_chunks:
            grid = self.cave_generator.generate_chunk(cx, cy)
            self.cave_chunks[(cx, cy)] = WorldChunk(cx, cy, grid)

    def _find_verified_portal_links(self, cx, cy, surface_grid, cave_grid):
        links = []
        min_dist_sq = (TILE_SIZE * 12) ** 2 
        
        for y in range(1, CHUNK_SIZE - 1):
            for x in range(1, CHUNK_SIZE - 1):
                if surface_grid[x][y] == BIOME_MTN_LOW:
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        if surface_grid[x+dx][y+dy] == BIOME_FOREST:
                            surf_tx, surf_ty = x + dx, y + dy
                            wx = (cx * CHUNK_SIZE + surf_tx) * TILE_SIZE
                            wy = (cy * CHUNK_SIZE + surf_ty) * TILE_SIZE
                            
                            random.seed(f"{SEED}_{wx}_{wy}_link")
                            if random.random() < PORTAL_CHANCE:
                                if any((l[0]-wx)**2 + (l[1]-wy)**2 < min_dist_sq for l in links): continue
                                if not self._has_right_spawn_square(surface_grid, surf_tx, surf_ty): continue

                                valid_cave_spot = self._find_valid_cave_configuration(cave_grid, surf_tx, surf_ty)
                                
                                if valid_cave_spot:
                                    cave_wx = (cx * CHUNK_SIZE + valid_cave_spot[0]) * TILE_SIZE
                                    cave_wy = (cy * CHUNK_SIZE + valid_cave_spot[1]) * TILE_SIZE
                                    links.append((wx, wy, cave_wx, cave_wy))
                                    break 
                    if len(links) > 0 and links[-1][0] == (cx * CHUNK_SIZE + x + dx) * TILE_SIZE: break 
        return links

    def _find_valid_cave_configuration(self, grid, start_x, start_y):
        queue = [(max(0, min(start_x, CHUNK_SIZE-1)), max(0, min(start_y, CHUNK_SIZE-1)))]
        visited = {queue[0]}
        for _ in range(400):
            if not queue: break
            cx, cy = queue.pop(0)
            
            if grid[cx][cy] in [BIOME_CAVE_ROOM, BIOME_CAVE_CORRIDOR]:
                has_wall = False
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE:
                        if grid[nx][ny] == BIOME_CAVE_WALL:
                            has_wall = True; break
                if has_wall and self._has_right_spawn_square(grid, cx, cy):
                    return (cx, cy)

            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < CHUNK_SIZE and 0 <= ny < CHUNK_SIZE and (nx, ny) not in visited:
                    visited.add((nx, ny)); queue.append((nx, ny))
        return None

    def _has_right_spawn_square(self, grid, px, py):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0: continue
                sx, sy = px + dx, py + dy 
                if 0 <= sx < CHUNK_SIZE and 0 <= sy < CHUNK_SIZE:
                    if grid[sx][sy] not in COLLISION_TILES and grid[sx][sy] != BIOME_DEEP_OCEAN:
                        neighbors = 0
                        for ndy in range(-1, 2):
                            for ndx in range(-1, 2):
                                if ndx == 0 and ndy == 0: continue
                                nsx, nsy = sx + ndx, sy + ndy
                                if 0 <= nsx < CHUNK_SIZE and 0 <= nsy < CHUNK_SIZE:
                                    if (nsx != px or nsy != py) and grid[nsx][nsy] not in COLLISION_TILES:
                                        neighbors += 1
                        if neighbors >= 1: return True 
        return False

    def _instantiate_portals(self, valid_links):
        for surf_x, surf_y, cave_x, cave_y in valid_links:
            if not any(p.rect.x == surf_x and p.rect.y == surf_y for p in self.surface_portals):
                p_surf = Portal(surf_x, surf_y, -1)
                p_surf.linked_pos = (cave_x, cave_y) 
                self.surface_portals.append(p_surf)

            if not any(p.rect.x == cave_x and p.rect.y == cave_y for p in self.cave_portals):
                p_cave = Portal(cave_x, cave_y, 0)
                p_cave.linked_pos = (surf_x, surf_y) 
                self.cave_portals.append(p_cave)

    # --- TELEPORTATION ---
    def check_portals(self, player):
        now = pygame.time.get_ticks()
        if now - self.last_teleport_time < self.teleport_cooldown: return False
        
        for portal in self.active_portals:
            if player.rect.colliderect(portal.rect.inflate(-2, -2)):
                self.teleport_player(player, portal)
                return True # Signal that teleport occurred
        return False

    def teleport_player(self, player, portal):
        self.last_teleport_time = pygame.time.get_ticks()
        dest_x, dest_y = (portal.linked_pos if portal.linked_pos else (portal.rect.x, portal.rect.y))

        self.current_layer = portal.target_layer
        self.get_chunk(int(dest_x // (CHUNK_SIZE * TILE_SIZE)), int(dest_y // (CHUNK_SIZE * TILE_SIZE)))

        spawn_x, spawn_y = self._find_verified_spawn_spot(dest_x, dest_y)
        self._emergency_safety_check(spawn_x, spawn_y)

        player.rect.topleft = (spawn_x, spawn_y)
        player.velocity = pygame.math.Vector2(0, 0) 
        print(f"✨ Arrived at {spawn_x}, {spawn_y}")

    def _find_verified_spawn_spot(self, px, py):
        cx, cy = int(px // (CHUNK_SIZE * TILE_SIZE)), int(py // (CHUNK_SIZE * TILE_SIZE))
        chunk = self.get_chunk(cx, cy)
        lx, ly = int((px % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE), int((py % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0: continue
                sx, sy = lx + dx, ly + dy
                if 0 <= sx < CHUNK_SIZE and 0 <= sy < CHUNK_SIZE:
                    if chunk.grid[sx][sy] not in COLLISION_TILES:
                        neighbors = 0
                        for ndy in range(-1, 2):
                            for ndx in range(-1, 2):
                                if ndx == 0 and ndy == 0: continue
                                nsx, nsy = sx + ndx, sy + ndy
                                if 0 <= nsx < CHUNK_SIZE and 0 <= nsy < CHUNK_SIZE:
                                    if (nsx != lx or nsy != ly) and chunk.grid[nsx][nsy] not in COLLISION_TILES:
                                        neighbors += 1
                        if neighbors >= 1:
                            return (cx * CHUNK_SIZE + sx) * TILE_SIZE, (cy * CHUNK_SIZE + sy) * TILE_SIZE
        return px, py

    def _emergency_safety_check(self, wx, wy):
        cx, cy = int(wx // (CHUNK_SIZE * TILE_SIZE)), int(wy // (CHUNK_SIZE * TILE_SIZE))
        chunk = self.get_chunk(cx, cy)
        lx, ly = int((wx % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE), int((wy % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        if 0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE:
            if chunk.grid[lx][ly] in COLLISION_TILES:
                chunk.grid[lx][ly] = BIOME_GRASS if self.current_layer == 0 else BIOME_CAVE_ROOM
                chunk.rebuild()

    def get_nearby_walls(self, rect):
        walls = []
        cx, cy = int(rect.centerx // (CHUNK_SIZE * TILE_SIZE)), int(rect.centery // (CHUNK_SIZE * TILE_SIZE))
        for y in range(cy-1, cy+2):
            for x in range(cx-1, cx+2):
                chunk = self.get_chunk(x, y)
                walls.extend(chunk.rects)
        return walls

    def draw_visible_chunks(self, screen, camera):
        cam_x, cam_y = -camera.camera.x, -camera.camera.y
        start_cx, start_cy = int(cam_x // (CHUNK_SIZE * TILE_SIZE)), int(cam_y // (CHUNK_SIZE * TILE_SIZE))
        end_cx, end_cy = start_cx + (WIDTH // (CHUNK_SIZE * TILE_SIZE)) + 2, start_cy + (HEIGHT // (CHUNK_SIZE * TILE_SIZE)) + 2
        for y in range(start_cy, end_cy):
            for x in range(start_cx, end_cx):
                chunk = self.get_chunk(x, y)
                ox, oy = x * CHUNK_SIZE * TILE_SIZE + camera.camera.x, y * CHUNK_SIZE * TILE_SIZE + camera.camera.y
                for lx in range(CHUNK_SIZE):
                    for ly in range(CHUNK_SIZE):
                        tile = chunk.grid[lx][ly]
                        if tile == BIOME_DEEP_OCEAN: continue 
                        rect = pygame.Rect(ox + lx * TILE_SIZE, oy + ly * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        if screen.get_rect().colliderect(rect):
                            pygame.draw.rect(screen, BIOME_COLORS.get(tile, (255,0,255)), rect)
        for p in self.active_portals: p.draw(screen, camera)
            
    def toggle_layer(self):
        if self.current_layer == 0: self.current_layer = -1
        else: self.current_layer = 0