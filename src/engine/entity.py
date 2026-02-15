# src/engine/entity.py
import pygame
from pygame.math import Vector2
from engine.physics import move
from engine.stats import AttributeManager
from settings import TILE_SIZE

class Entity:
    def __init__(self, x, y, color):
        # Physical Properties
        self.rect = pygame.Rect(x, y, TILE_SIZE - 2, TILE_SIZE - 2)
        self.velocity = Vector2(0, 0)
        self.color = color
        
        # RPG Stats (Every entity has stats)
        self.stats = AttributeManager()
        
        # State
        self.is_alive = True

    def apply_physics(self, walls):
        """Shared physics logic"""
        self.rect, _ = move(self.rect, self.velocity, walls)

    def draw(self, screen, camera):
        """Shared drawing logic"""
        if self.is_alive:
            draw_rect = camera.apply(self.rect)
            pygame.draw.rect(screen, self.color, draw_rect)