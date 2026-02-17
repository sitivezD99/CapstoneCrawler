# src/engine/camera.py
import pygame
import random
from settings import *

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        
        # Shake Variables
        self.shake_duration = 0
        self.shake_magnitude = 0
        self.offset = pygame.math.Vector2(0, 0)

    def apply(self, entity_rect):
        """Returns a rect shifted by the camera offset."""
        return entity_rect.move(self.camera.topleft)

    def update(self, target):
        """Follows the target (player) smoothly."""
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)

        # Smooth camera movement (Lerp)
        self.camera.x += (x - self.camera.x) * 0.1
        self.camera.y += (y - self.camera.y) * 0.1
        
        # Apply Screen Shake
        if self.shake_duration > 0:
            self.shake_duration -= 1
            rx = random.randint(-self.shake_magnitude, self.shake_magnitude)
            ry = random.randint(-self.shake_magnitude, self.shake_magnitude)
            self.camera.x += rx
            self.camera.y += ry

    def trigger_shake(self, duration=10, magnitude=5):
        """Call this when a hit lands!"""
        self.shake_duration = duration
        self.shake_magnitude = magnitude