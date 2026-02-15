# src/engine/camera.py
import pygame
from settings import WIDTH, HEIGHT

class Camera:
    def __init__(self, width, height):
        # This 'self.camera' is the rectangle the WorldManager is looking for!
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, target):
        """
        Applies the camera offset to a target. 
        Target can be an Entity (with .rect) or a raw pygame.Rect.
        """
        if hasattr(target, 'rect'):
            return target.rect.move(self.camera.topleft)
        elif isinstance(target, pygame.Rect):
            return target.move(self.camera.topleft)
        return target # Fallback

    def update(self, target):
        """
        Follows the target (Player).
        """
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)
        
        # Update the internal viewport rect
        self.camera = pygame.Rect(x, y, self.width, self.height)