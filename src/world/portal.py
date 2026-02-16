import pygame
from settings import *

class Portal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.color = PORTAL_COLOR
        
    def update(self, dt):
        # We could add a particle effect here later!
        pass

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        # Draw the black hole
        pygame.draw.rect(screen, self.color, draw_rect)
        # Draw a small outline so it's visible against dark rock
        pygame.draw.rect(screen, (100, 100, 100), draw_rect, 1)