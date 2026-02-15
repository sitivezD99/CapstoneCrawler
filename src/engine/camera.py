import pygame
from pygame.math import Vector2
from settings import *

class Camera:
    def __init__(self, width, height):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.offset = Vector2(0, 0)
        self.target_offset = Vector2(0, 0)

    def apply(self, entity_rect):
        """Offset a rect relative to the camera"""
        return entity_rect.move(int(-self.offset.x), int(-self.offset.y))

    def update(self, target):
        """
        Follow the target (player) with Lerp smoothing.
        target: The Player object
        """
        # 1. Calculate ideal position (Center the player)
        target_x = target.rect.centerx - int(WIDTH / 2)
        target_y = target.rect.centery - int(HEIGHT / 2)
        
        self.target_offset.x = target_x
        self.target_offset.y = target_y

        # 2. Determine Smoothness (Context Aware)
        # If player is moving fast, camera snaps tighter.
        # If player is exploring slowly, camera drifts (Lerp).
        lerp_speed = 0.1 # Standard "Dreamy" follow
        
        # 3. Apply Vector Lerp
        self.offset += (self.target_offset - self.offset) * lerp_speed