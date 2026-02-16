# src/world/enemy.py
import pygame
from pygame.math import Vector2
from settings import *
from engine.ai import Pathfinder

class EnemyStats:
    """
    A simple stats container for enemies that mimics the AttributeManager.
    This fixes the 'AttributeError: has no attribute modify_hp' crash.
    """
    def __init__(self, hp, damage):
        self.max_hp = hp
        self.current_hp = hp
        self.damage = damage

    def modify_hp(self, amount):
        """
        Safely modifies HP and keeps it within bounds.
        """
        self.current_hp += amount
        
        # Cap at Max
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp
            
        # Cap at Min (Death check is handled by the Enemy class)
        if self.current_hp < 0:
            self.current_hp = 0

class Enemy:
    def __init__(self, x, y):
        # Physics
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.position = Vector2(x, y) # Float position for smooth movement
        self.velocity = Vector2(0, 0)
        self.speed = 1.5 
        
        # Stats
        self.is_alive = True
        # FIX: Use the real class instead of the dummy object
        self.stats = EnemyStats(hp=20, damage=5)
        
        # AI
        self.path = []
        self.path_timer = 0
        self.aggro_radius = 600

    def update(self, dt, player, world, enemies):
        """
        AI Logic: Chase Player -> Boid Separation -> Wall Collision
        """
        # Death Check
        if self.stats.current_hp <= 0:
            self.is_alive = False
            return

        dist_to_player = self.position.distance_to(Vector2(player.rect.center))

        if dist_to_player < self.aggro_radius:
            self.state_chase(dt, player, world, enemies)
        else:
            self.velocity = Vector2(0, 0) # Idle

        # Apply Physics
        self.position += self.velocity
        self.rect.topleft = (int(self.position.x), int(self.position.y))

    def state_chase(self, dt, player, world, enemies):
        # 1. Update Path (Every 0.5 seconds to save CPU)
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.path_timer = 0.5
            # Pathfinder uses world.get_chunk() safely
            self.path = Pathfinder.get_path(self.position, Vector2(player.rect.center), world)

        # 2. Follow Path
        target_pos = Vector2(player.rect.center)
        if self.path:
            target_pos = self.path[0]
            # If we reached the node, remove it
            if self.position.distance_to(target_pos) < 10:
                self.path.pop(0)

        # 3. Calculate Steering
        direction = (target_pos - self.position)
        if direction.length() > 0:
            direction = direction.normalize()
        
        self.velocity = direction * self.speed

        # 4. Soft Collision (Boids Separation)
        # Don't stack on top of other enemies
        for other in enemies:
            if other != self:
                dist = self.position.distance_to(other.position)
                if dist < TILE_SIZE: # Too close!
                    push = (self.position - other.position)
                    if push.length() > 0:
                        self.velocity += push.normalize() * 1.0

        # 5. Wall Collision
        # Look ahead to stop at walls
        next_pos = self.position + self.velocity * 5 
        
        chunk_x = int(next_pos.x // (CHUNK_SIZE * TILE_SIZE))
        chunk_y = int(next_pos.y // (CHUNK_SIZE * TILE_SIZE))
        
        # Use UniverseManager to get the correct chunk (Surface or Cave)
        chunk = world.get_chunk(chunk_x, chunk_y)

        local_x = int((next_pos.x % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
        local_y = int((next_pos.y % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)

        # Bounds check
        if 0 <= local_x < CHUNK_SIZE and 0 <= local_y < CHUNK_SIZE:
            tile_id = chunk.grid[local_x][local_y]
            if tile_id in COLLISION_TILES:
                self.velocity *= 0 # Stop! Wall ahead.

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        # Draw Enemy (Red Square)
        pygame.draw.rect(screen, (200, 50, 50), draw_rect)
        
        # Draw Health Bar
        if self.stats.current_hp < self.stats.max_hp:
            hp_pct = self.stats.current_hp / self.stats.max_hp
            bar_w = TILE_SIZE
            bar_h = 4
            bar_x = draw_rect.x
            bar_y = draw_rect.y - 6
            
            # Background