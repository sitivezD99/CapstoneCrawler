# src/world/portal.py
import pygame
from settings import *

class Portal:
    def __init__(self, x, y, target_layer):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.target_layer = target_layer # 0 for Surface, -1 for Caves
        
        # Smart Linking: Where exactly does this door lead?
        # If None, it hasn't been discovered/linked yet.
        self.linked_pos = None 
        
        # Visuals
        self.color = (0, 0, 0) if target_layer == -1 else (0, 255, 255) # Black=Down, Cyan=Up

    def draw(self, screen, camera):
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect)
        # Simple outline
        pygame.draw.rect(screen, (255, 255, 255), draw_rect, 1)