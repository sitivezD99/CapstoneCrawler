# src/world/enemy.py
import pygame
from pygame.math import Vector2
from settings import *
from engine.ai import Pathfinder
from engine.physics import move_and_slide 

class EnemyStats:
    def __init__(self, hp, damage):
        self.max_hp = hp
        self.current_hp = hp
        self.damage = damage

    def modify_hp(self, amount):
        self.current_hp += amount
        if self.current_hp > self.max_hp: self.current_hp = self.max_hp
        if self.current_hp < 0: self.current_hp = 0

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.position = Vector2(x, y) 
        self.velocity = Vector2(0, 0)
        self.speed = 1.5 
        self.is_alive = True
        self.stats = EnemyStats(hp=20, damage=5)
        self.path = []
        self.path_timer = 0
        self.aggro_radius = 600

    def update(self, dt, player, world, enemies):
        if self.stats.current_hp <= 0:
            self.is_alive = False
            return

        dist_to_player = self.position.distance_to(Vector2(player.rect.center))

        if dist_to_player < self.aggro_radius:
            self.state_chase(dt, player, world, enemies)
        else:
            self.velocity = Vector2(0, 0)

        # PHYSICS FIX: Get nearby walls and slide
        nearby_walls = self.get_nearby_walls(world)
        self.rect = move_and_slide(self.rect, self.velocity, nearby_walls)
        
        self.position.x = self.rect.x
        self.position.y = self.rect.y

    def get_nearby_walls(self, world):
        cx = int(self.rect.centerx // (CHUNK_SIZE * TILE_SIZE))
        cy = int(self.rect.centery // (CHUNK_SIZE * TILE_SIZE))
        walls = []
        for y in range(cy - 1, cy + 2):
            for x in range(cx - 1, cx + 2):
                chunk = world.get_chunk(x, y)
                walls.extend(chunk.rects)
        return walls

    def state_chase(self, dt, player, world, enemies):
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.path_timer = 0.5
            self.path = Pathfinder.get_path(self.position, Vector2(player.rect.center), world)

        target_pos = Vector2(player.rect.center)
        if self.path:
            target_pos = self.path[0]
            if self.position.distance_to(target_pos) < 10:
                self.path.pop(0)

        direction = (target_pos - self.position)
        if direction.length() > 0:
            direction = direction.normalize()
        
        self.velocity = direction * self.speed

        for other in enemies:
            if other != self:
                dist = self.position.distance_to(other.position)
                if dist < TILE_SIZE: 
                    push = (self.position - other.position)
                    if push.length() > 0:
                        self.velocity += push.normalize() * 1.5

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, (200, 50, 50), draw_rect)
        if self.stats.current_hp < self.stats.max_hp:
            hp_pct = self.stats.current_hp / self.stats.max_hp
            bar_w = TILE_SIZE
            bar_h = 4
            bar_x = draw_rect.x
            bar_y = draw_rect.y - 6
            pygame.draw.rect(screen, (50, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_w * hp_pct, bar_h))