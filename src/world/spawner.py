# src/world/spawner.py
import pygame
import random
from settings import *
from world.enemy import Enemy

class Spawner:
    @staticmethod
    def spawn_wave(dungeon, start_tile_x, start_tile_y):
        """
        Enforces the Law of the Cavern using Generator Math.
        """
        # 1. THE FUNDAMENTAL FIX: Ask the Generator directly.
        # This bypasses flood fill errors. If it's a tunnel, this returns False.
        if not dungeon.generator.is_tile_in_room(start_tile_x, start_tile_y):
            # print("⛔ Aborted: Player is in a Tunnel or Wall.")
            return []

        # 2. If valid, we still flood fill just to find a nice spawnable floor area
        open_tiles = []
        stack = [(start_tile_x, start_tile_y)]
        visited = set()
        visited.add((start_tile_x, start_tile_y))
        
        count = 0
        limit = 300 
        
        while stack and count < limit:
            cx, cy = stack.pop()
            open_tiles.append((cx, cy))
            count += 1
            
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in visited:
                    chunk_x = nx // CHUNK_SIZE
                    chunk_y = ny // CHUNK_SIZE
                    chunk = dungeon.get_chunk(chunk_x, chunk_y)
                    lx = nx % CHUNK_SIZE
                    ly = ny % CHUNK_SIZE
                    
                    if 0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE:
                        if chunk.grid[ly][lx] == 1: 
                            visited.add((nx, ny))
                            stack.append((nx, ny))

        # 3. Calculate Center (Spawn monsters in the middle of the room)
        avg_x = sum(t[0] for t in open_tiles) // count
        avg_y = sum(t[1] for t in open_tiles) // count
        
        center_pixel_x = avg_x * TILE_SIZE
        center_pixel_y = avg_y * TILE_SIZE

        # Scale Difficulty
        enemy_count = 2
        if count > 80: enemy_count = 3
        if count > 150: enemy_count = 5
        
        print(f"⚔️ VALID ROUND ROOM. Spawning {enemy_count} enemies at Centroid.")
        
        enemies = []
        for _ in range(enemy_count):
            angle = random.uniform(0, 6.28)
            dist = random.uniform(20, 80)
            
            # Fixed the syntax error here
            vec_offset = pygame.math.Vector2(1, 0).rotate_rad(angle)
            spawn_x = center_pixel_x + int(dist * vec_offset.x)
            spawn_y = center_pixel_y + int(dist * vec_offset.y)
            
            # Final Wall Check
            dummy_rect = pygame.Rect(spawn_x, spawn_y, 20, 20)
            walls = dungeon.get_nearby_walls(dummy_rect)
            if dummy_rect.collidelist(walls) == -1:
                enemies.append(Enemy(spawn_x, spawn_y))
            
        return enemies