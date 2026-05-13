# src/engine/entity.py
import pygame
from pygame.math import Vector2
from engine.physics import move_and_slide

class Entity:
    def __init__(self, x, y, w, h, color):
        # Physical Properties based on custom sandbox sizes
        self.rect = pygame.Rect(x, y, w, h)
        self.velocity = Vector2(0, 0)
        self.color = color
        
        # State
        self.is_alive = True

    def apply_physics(self, walls):
        """Shared physics logic using the Corner Sliding system"""
        self.rect = move_and_slide(self.rect, self.velocity, walls)

    def draw(self, screen, camera):
        """Shared drawing logic"""
        if self.is_alive:
            draw_rect = camera.apply(self.rect)
            pygame.draw.rect(screen, self.color, draw_rect)