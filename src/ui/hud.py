# src/ui/hud.py
import pygame

class HUD:
    def __init__(self):
        # Upgrade: Using sleek System Fonts instead of Pygame's default pixel font
        # It tries Trebuchet MS first, then falls back to Tahoma or Arial.
        self.font_main = pygame.font.SysFont('trebuchetms, tahoma, arial', 28, bold=True)
        self.font_small = pygame.font.SysFont('trebuchetms, tahoma, arial', 20, bold=True)
        
        # We pre-create a surface for the "Glass Panel" background to save performance
        self.panel_surface = pygame.Surface((380, 220), pygame.SRCALPHA)
        # Draw a semi-transparent dark grey rectangle with rounded corners
        pygame.draw.rect(self.panel_surface, (20, 20, 25, 180), self.panel_surface.get_rect(), border_radius=12)

    def _draw_modern_bar(self, screen, x, y, width, height, ratio, base_color, label=""):
        # 1. Math Safety: Clamp ratio perfectly
        safe_ratio = max(0.0, min(1.0, float(ratio)))
        
        # 2. Empty Track Background
        pygame.draw.rect(screen, (35, 35, 40), (x, y, width, height), border_radius=6)
        
        # 3. Active Fill with Glossy 3D Effect
        if safe_ratio > 0:
            fill_width = int(width * safe_ratio)
            fill_rect = pygame.Rect(x, y, fill_width, height)
            pygame.draw.rect(screen, base_color, fill_rect, border_radius=6)
            
            # Draw a highlight line on the top half for a glossy/bevel look
            highlight_color = (min(255, base_color[0] + 50), 
                               min(255, base_color[1] + 50), 
                               min(255, base_color[2] + 50))
            highlight_rect = pygame.Rect(x, y, fill_width, height // 2)
            pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=6)
        
        # 4. Clean Outer Border
        pygame.draw.rect(screen, (80, 80, 90), (x, y, width, height), 2, border_radius=6)
        
        # 5. Crisp Label Rendering with strict Drop Shadows
        if label:
            shadow = self.font_small.render(label, True, (0, 0, 0))
            text = self.font_small.render(label, True, (240, 240, 240))
            screen.blit(shadow, (x + width + 17, y + 3))
            screen.blit(text, (x + width + 15, y + 1))

    def draw(self, screen, player, hex_ui):
        # Draw the sleek glass panel backdrop in the top-left corner
        screen.blit(self.panel_surface, (15, 15))

        start_x = 35
        start_y = 35
        bar_w = 200

        # 1. Health Bar (Rich Crimson)
        hp_ratio = player.attributes.current_hp / player.attributes.max_hp
        self._draw_modern_bar(screen, start_x, start_y, bar_w, 24, hp_ratio, (180, 40, 40))
        
        # Crisp HP Text superimposed on the bar
        hp_str = f"{int(player.attributes.current_hp)} / {player.attributes.max_hp} HP"
        # Center the text mathematically inside the health bar
        text_w, text_h = self.font_small.size(hp_str)
        text_x = start_x + (bar_w // 2) - (text_w // 2)
        text_y = start_y + (24 // 2) - (text_h // 2)
        
        screen.blit(self.font_small.render(hp_str, True, (0, 0, 0)), (text_x + 1, text_y + 1))
        screen.blit(self.font_small.render(hp_str, True, (255, 255, 255)), (text_x, text_y))
        
        start_y += 45

        # 2. XP Bar (Vibrant Gold)
        xp_ratio = 1.0 if player.attributes.level >= 20 else player.attributes.xp / player.attributes.xp_next
        self._draw_modern_bar(screen, start_x, start_y, bar_w, 14, xp_ratio, (218, 165, 32), "XP") 
        
        start_y += 35

        # --- SKILLS HELPER LOGIC ---
        def get_skill_data(timer, base_cd, name):
            haste = 1.0 - min(hex_ui.skill_stats.get(name, {}).get('Haste', 0), 0.5)
            max_time = base_cd * haste
            if max_time <= 0: return 1.0
            return 1.0 - (timer / max_time)

        # 3. Skill 1: Hammer (Burnt Orange)
        if player.attributes.level >= 5:
            ratio = get_skill_data(player.skill_1_cooldown_timer, player.skill_1_cooldown, "HAMMER (X)")
            color = (220, 110, 0) if ratio >= 1.0 else (90, 90, 90)
            self._draw_modern_bar(screen, start_x, start_y, bar_w, 16, ratio, color, "HAMMER [X]")
            start_y += 30
            
        # 4. Skill 2: Stun (Royal Purple)
        if player.attributes.level >= 10:
            ratio = get_skill_data(player.skill_2_cooldown_timer, player.skill_2_cooldown, "STUN (Y)")
            color = (138, 43, 226) if ratio >= 1.0 else (90, 90, 90)
            self._draw_modern_bar(screen, start_x, start_y, bar_w, 16, ratio, color, "STUN [Y]")
            start_y += 30
            
        # 5. Skill 3: Whirlwind/Spin (Emerald Green)
        if player.attributes.level >= 15:
            ratio = get_skill_data(player.skill_3_cooldown_timer, player.skill_3_cooldown, "WHIRLWIND (B)")
            color = (46, 175, 87) if ratio >= 1.0 else (90, 90, 90)
            self._draw_modern_bar(screen, start_x, start_y, bar_w, 16, ratio, color, "SPIN [B]")

        # 6. Global Stats & Prompts (Top Right of Screen)
        # Using a sleek translucent background for the stats too
        stat_str = f" LVL {player.attributes.level} | DEF: {int(player.attributes.defense)} "
        stat_surf = self.font_main.render(stat_str, True, (255, 255, 255))
        
        stat_bg = pygame.Surface((stat_surf.get_width() + 20, stat_surf.get_height() + 10), pygame.SRCALPHA)
        pygame.draw.rect(stat_bg, (20, 20, 25, 180), stat_bg.get_rect(), border_radius=8)
        
        # Position dynamically based on screen width
        screen_w = screen.get_width()
        box_x = screen_w - stat_bg.get_width() - 20
        box_y = 20
        
        screen.blit(stat_bg, (box_x, box_y))
        screen.blit(stat_surf, (box_x + 10, box_y + 5))
        
        # Menu Prompt
        prompt_str = "PRESS [START] FOR MENU"
        prompt_surf = self.font_small.render(prompt_str, True, (150, 220, 255))
        screen.blit(self.font_small.render(prompt_str, True, (0, 0, 0)), (box_x + 12, box_y + 52)) # Shadow
        screen.blit(prompt_surf, (box_x + 10, box_y + 50))