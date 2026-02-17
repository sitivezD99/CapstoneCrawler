# src/world/spawner.py
import pygame
import random
from settings import *
from world.enemy import Enemy

class Spawner:
    @staticmethod
    def spawn_enemies(world_manager, player):
        """
        Global Spawning System.
        Automatically handles infinite world spawning.
        """
        return Spawner._spawn_on_island(world_manager, player)

    @staticmethod
    def _spawn_on_island(world, player):
        """
        Randomly spawn enemies around the player in valid open terrain.
        """
        enemies = []
        target_count = 1  
        attempts = 10     
        
        spawn_radius_min = 400 
        spawn_radius_max = 700 
        
        for _ in range(attempts):
            if len(enemies) >= target_count: break
            
            # 1. Pick a random angle and distance
            angle = random.uniform(0, 6.28)
            dist = random.uniform(spawn_radius_min, spawn_radius_max)
            
            offset = pygame.math.Vector2(1, 0).rotate_rad(angle) * dist
            spawn_x = player.rect.centerx + offset.x
            spawn_y = player.rect.centery + offset.y
            
            # 2. Check Validity (Must be land, not wall, not water)
            if Spawner._is_valid_spawn_spot(world, spawn_x, spawn_y):
                enemies.append(Enemy(spawn_x, spawn_y))
                # print(f"🦀 Spawning Enemy at {int(spawn_x)}, {int(spawn_y)}")
                
        return enemies

    @staticmethod
    def _is_valid_spawn_spot(world, x, y):
        chunk_x = int(x // (CHUNK_SIZE * TILE_SIZE))
        chunk_y = int(y // (CHUNK_SIZE * TILE_SIZE))
        
        chunk = world.get_chunk(chunk_x, chunk_y)
        
        local_x = int((x % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        local_y = int((y % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        
        if not (0 <= local_x < CHUNK_SIZE and 0 <= local_y < CHUNK_SIZE):
            return False
            
        tile_id = chunk.grid[local_x][local_y] 
        
        if tile_id in COLLISION_TILES: return False
        if tile_id == BIOME_DEEP_OCEAN or tile_id == BIOME_OCEAN: return False
            
        return True