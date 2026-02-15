# src/world/enemy.py
import pygame
from pygame.math import Vector2
from engine.entity import Entity
from engine.ai import Pathfinder
from engine.physics import move_and_slide
from settings import TILE_SIZE

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 200, 0))
        self.target = None
        self.path = []
        self.path_timer = 0
        self.agro_radius = 600
        
        # Stats
        self.stats.agility = 4
        self.stats.update_derived_stats()
        
        # New: Hard Speed Limit (Pixels per Frame)
        self.max_speed = 3.0 

    def update(self, dt, player, dungeon, all_enemies):
        dist = Vector2(self.rect.center).distance_to(player.rect.center)

        if dist < self.agro_radius:
            self.state_chase(dt, player, dungeon, all_enemies)
        else:
            self.path = [] 

        self.apply_physics(dungeon.get_nearby_walls(self.rect))

    def state_chase(self, dt, player, dungeon, all_enemies):
        center = Vector2(self.rect.center)
        
        # 1. Pathfinding
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.path = Pathfinder.get_path(center, Vector2(player.rect.center), dungeon)
            self.path_timer = 0.5 

        steering = Vector2(0, 0)

        # Force A: Follow Path
        if self.path:
            next_node = self.path[0]
            dir_to_node = (next_node - center)
            if dir_to_node.length() < 16:
                self.path.pop(0)
            else:
                steering += dir_to_node.normalize() * 1.0

        # Force B: Separation
        count = 0
        separation = Vector2(0, 0)
        for other in all_enemies:
            if other != self and other.is_alive:
                dist = center.distance_to(other.rect.center)
                if dist < 40:
                    push = center - Vector2(other.rect.center)
                    if push.length() > 0:
                        separation += push.normalize() / dist 
                        count += 1
        if count > 0:
            steering += separation * 50.0

        # Force C: Wall Avoidance
        if self.velocity.length() > 0:
            look_ahead = self.velocity.normalize() * 30 
            sensor_point = center + look_ahead
            gx = int(sensor_point.x // TILE_SIZE)
            gy = int(sensor_point.y // TILE_SIZE)
            chunk_x = gx // 32
            chunk_y = gy // 32
            chunk = dungeon.chunks.get((chunk_x, chunk_y))
            if chunk:
                lx = gx % 32
                ly = gy % 32
                if chunk.grid[ly][lx] == 0:
                    wall_center = Vector2(gx * TILE_SIZE + 16, gy * TILE_SIZE + 16)
                    avoid = center - wall_center
                    if avoid.length() > 0:
                        steering += avoid.normalize() * 80.0

        # Apply Steering
        if steering.length() > 0:
            steering = steering.normalize()
            self.velocity = self.velocity.lerp(steering * 3.0, 0.1) # Target Speed 3.0
        
        # HARD CLAMP (Safety Brake)
        if self.velocity.length() > 3.0:
            self.velocity.scale_to_length(3.0)

    def apply_physics(self, walls):
        self.rect = move_and_slide(self.rect, self.velocity, walls)