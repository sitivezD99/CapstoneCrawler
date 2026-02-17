# src/ui/hud.py
import pygame
from settings import *

class HUD:
    def __init__(self, player):
        self.player = player
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 40)

    def draw(self, screen):
        # --- HEALTH BAR (Top Left) ---
        bar_x = 20
        bar_y = 20
        bar_w = 200
        bar_h = 20
        
        # Calculate Percentage
        hp_pct = self.player.stats.current_hp / self.player.stats.max_hp
        hp_pct = max(0, min(1, hp_pct)) # Clamp between 0 and 1
        
        # Draw Background (Dark Red)
        pygame.draw.rect(screen, (50, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        # Draw Foreground (Bright Red)
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_w * hp_pct, bar_h))
        # Draw Border (White)
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2)
        
        # Text: HP 100/100
        hp_text = f"HP {int(self.player.stats.current_hp)}/{self.player.stats.max_hp}"
        text_surf = self.font.render(hp_text, True, (255, 255, 255))
        screen.blit(text_surf, (bar_x + 5, bar_y + 25))

        # --- XP BAR (Bottom Center) ---
        xp_w = 400
        xp_h = 15
        xp_x = (WIDTH // 2) - (xp_w // 2)
        xp_y = HEIGHT - 40
        
        # Calculate Percentage
        # Guard against divide by zero
        if self.player.xp_next_level > 0:
            xp_pct = self.player.xp / self.player.xp_next_level
        else:
            xp_pct = 0
            
        xp_pct = max(0, min(1, xp_pct))
        
        # Background (Dark Blue)
        pygame.draw.rect(screen, (0, 0, 50), (xp_x, xp_y, xp_w, xp_h))
        # Foreground (Gold/Yellow)
        pygame.draw.rect(screen, (255, 215, 0), (xp_x, xp_y, xp_w * xp_pct, xp_h))
        # Border
        pygame.draw.rect(screen, (255, 255, 255), (xp_x, xp_y, xp_w, xp_h), 2)
        
        # Level Badge
        level_text = self.large_font.render(f"LVL {self.player.level}", True, (255, 215, 0))
        # Shadow for readability
        shadow_text = self.large_font.render(f"LVL {self.player.level}", True, (0, 0, 0))
        
        screen.blit(shadow_text, (xp_x - 78, xp_y - 10))
        screen.blit(level_text, (xp_x - 80, xp_y - 12))