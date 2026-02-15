# src/world/enemy.py
import pygame
from pygame.math import Vector2
from engine.entity import Entity
from engine.ai import Pathfinder
from settings import PLAYER_SPEED

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 200, 0)) # Green
        self.target = None
        self.path = []
        self.path_timer = 0
        self.agro_radius = 500
        # AGI 5 -> Speed 0.75.
        self.stats.agility = 5 
        self.stats.update_derived_stats()

    def update(self, dt, player, dungeon):
        dist = self.rect.center - Vector2(player.rect.center)
        dist_len = dist.length()

        if dist_len < self.agro_radius:
            self.state_chase(dt, player, dungeon)
        else:
            self.path = [] 

        self.apply_physics(dungeon.get_nearby_walls(self.rect))

    def state_chase(self, dt, player, dungeon):
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.path = Pathfinder.get_path(Vector2(self.rect.center), Vector2(player.rect.center), dungeon)
            self.path_timer = 0.5

        if self.path and len(self.path) > 0:
            next_node = self.path[0]
            direction = (next_node - Vector2(self.rect.center))
            
            dist_to_node = direction.length()
            
            # FIX: Increase snap distance to 10px so they don't overshoot/vibrate
            if dist_to_node < 10:
                self.path.pop(0) 
            else:
                direction = direction.normalize()
                # FIX: Reduced multiplier from 20 to 5
                # Result: ~3.75 pixels/frame (Player is ~6)
                self.velocity = direction * self.stats.speed * 5
        
        self.velocity *= 0.85