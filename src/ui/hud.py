# src/ui/hud.py
import pygame
from settings import *

class HUD:
    def __init__(self, player):
        self.player = player
        self.font = pygame.font.SysFont("Arial", 16, bold=True)

    def draw(self, screen):
        stats = self.player.stats
        
        # --- HEALTH BAR (Top Left) ---
        bar_x, bar_y = 20, 20
        bar_w, bar_h = 200, 20
        
        # Background (Grey)
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        
        # Foreground (Red) - Calculated ratio
        hp_ratio = stats.current_hp / stats.max_hp
        pygame.draw.rect(screen, (200, 0, 0), (bar_x, bar_y, bar_w * hp_ratio, bar_h))
        
        # Text
        text = self.font.render(f"HP: {int(stats.current_hp)} / {stats.max_hp}", True, (255, 255, 255))
        screen.blit(text, (bar_x + 5, bar_y + 2))

        # --- XP BAR (Below HP) ---
        xp_y = bar_y + 30
        
        # Background (Grey)
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, xp_y, bar_w, bar_h))
        
        # Foreground (Gold)
        xp_ratio = stats.xp / stats.xp_next
        pygame.draw.rect(screen, (255, 215, 0), (bar_x, xp_y, bar_w * xp_ratio, bar_h))
        
        # Text
        level_text = self.font.render(f"LVL {stats.level} | XP: {int(stats.xp)}/{stats.xp_next}", True, (20, 20, 20))
        screen.blit(level_text, (bar_x + 5, xp_y + 2))