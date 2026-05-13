# dev_vault_ui.py
import pygame
import math
import copy
from pygame.math import Vector2
from settings import *

class DevVaultUI:
    def __init__(self, global_db):
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        try: self.icon_font = pygame.font.SysFont(['segoe ui emoji', 'apple color emoji', 'noto color emoji'], 32)
        except: self.icon_font = self.font
        
        self.items = global_db.get_all_items_list()
        self.cursor_idx = 0
        
        self.cols = 10
        self.rows_visible = 6
        self.slots_per_page = self.cols * self.rows_visible
        
        self.stick_x_pressed = False
        self.stick_y_pressed = False
        
        # AAA Kinetics
        self.visual_scroll = 0.0
        
        # Quantity Selector State
        self.is_selecting_qty = False
        self.spawn_qty = 1

    def reset(self):
        self.cursor_idx = 0
        self.is_selecting_qty = False
        self.spawn_qty = 1

    def update(self, dt):
        """AAA Kinetics: Smooth smartphone-style scroll for the developer vault."""
        target_scroll = (self.cursor_idx // self.cols) - (self.rows_visible - 1)
        if target_scroll < 0: target_scroll = 0
        self.visual_scroll += (target_scroll - self.visual_scroll) * min(dt * 15.0, 1.0)

    def _wrap_left(self, max_idx):
        if max_idx < 0: return 0
        row_start = (self.cursor_idx // self.cols) * self.cols
        row_end = min(max_idx, row_start + self.cols - 1)
        return row_end if self.cursor_idx == row_start else self.cursor_idx - 1

    def _wrap_right(self, max_idx):
        if max_idx < 0: return 0
        row_start = (self.cursor_idx // self.cols) * self.cols
        row_end = min(max_idx, row_start + self.cols - 1)
        return row_start if self.cursor_idx == row_end else self.cursor_idx + 1

    def handle_input(self, event, player_inventory):
        is_back = (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]) or \
                  (event.type == pygame.JOYBUTTONDOWN and event.button == 1)

        if is_back:
            if self.is_selecting_qty:
                self.is_selecting_qty = False
                return None
            else:
                return "BACK"

        # --- THE ANTI-GHOSTING CLAMP ---
        # If the vault is empty, do nothing safely.
        if not hasattr(self, 'items') or len(self.items) == 0:
            return None
            
        max_idx = len(self.items) - 1
        # This one line permanently prevents the cursor from going out of bounds and breaking the UI
        self.cursor_idx = max(0, min(self.cursor_idx, max_idx))

        dx, dy = 0, 0
        action_pressed = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: dx = -1
            elif event.key == pygame.K_RIGHT: dx = 1
            elif event.key == pygame.K_UP: dy = -1
            elif event.key == pygame.K_DOWN: dy = 1
            elif event.key == pygame.K_RETURN: action_pressed = True
        elif event.type == pygame.JOYHATMOTION:
            hx, hy = event.value
            dx = hx
            dy = -hy 
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value > 0.6 and not self.stick_x_pressed: dx = 1; self.stick_x_pressed = True
                elif event.value < -0.6 and not self.stick_x_pressed: dx = -1; self.stick_x_pressed = True
                elif abs(event.value) < 0.2: self.stick_x_pressed = False
            elif event.axis == 1:
                if event.value > 0.6 and not self.stick_y_pressed: dy = 1; self.stick_y_pressed = True
                elif event.value < -0.6 and not self.stick_y_pressed: dy = -1; self.stick_y_pressed = True
                elif abs(event.value) < 0.2: self.stick_y_pressed = False
        elif event.type == pygame.JOYBUTTONDOWN and event.button == 0:
            action_pressed = True

        # --- QUANTITY SELECTOR STATE ---
        if self.is_selecting_qty:
            sel_item = self.items[self.cursor_idx]
            max_q = int(getattr(sel_item, 'max_stack', 99)) # Safely checks max stack
            
            if dx == -1: self.spawn_qty -= 1
            elif dx == 1: self.spawn_qty += 1
            elif dy == -1: self.spawn_qty -= 10
            elif dy == 1: self.spawn_qty += 10
            
            # Mathematical clamping
            if self.spawn_qty < 1: self.spawn_qty = 1
            if self.spawn_qty > max_q: self.spawn_qty = max_q
            
            if action_pressed:
                # Fast spawning logic loops the safe add_item logic
                for _ in range(self.spawn_qty):
                    new_item = copy.copy(sel_item)
                    player_inventory.add_item(new_item)
                self.is_selecting_qty = False
                return "SPAWNED"
            return None

        # --- NORMAL NAVIGATION STATE ---
        if dy == -1: self.cursor_idx = max(0, self.cursor_idx - self.cols)
        elif dy == 1: self.cursor_idx = min(max_idx, self.cursor_idx + self.cols)
        elif dx == -1: self.cursor_idx = self._wrap_left(max_idx)
        elif dx == 1: self.cursor_idx = self._wrap_right(max_idx)

        # Trigger Quantity Prompt
        if action_pressed:
            self.is_selecting_qty = True
            self.spawn_qty = 1
            
        return None

    def draw(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((30, 10, 10, 250)) 
        screen.blit(overlay, (0,0))

        screen.blit(self.title_font.render("DEVELOPER VAULT (ALL ITEMS)", True, (255,100,100)), (50, 40))

        total_items = len(self.items)
        start_x, start_y = 50, 100
        slot_size, spacing = 70, 15
        
        # AAA Clipping for smooth scroll
        clip_h = self.rows_visible * (slot_size + spacing)
        screen.set_clip(pygame.Rect(40, 90, WIDTH - 80, clip_h + 20))
        
        for i, item in enumerate(self.items): 
            col, row = i % self.cols, i // self.cols
            x = start_x + col * (slot_size + spacing)
            y = start_y + (row - self.visual_scroll) * (slot_size + spacing)
            
            if y > start_y + clip_h or y < start_y - slot_size: continue
            
            rect = pygame.Rect(x, y, slot_size, slot_size)
            is_selected = (i == self.cursor_idx)
            
            pygame.draw.rect(screen, (60, 60, 70) if is_selected else (30, 30, 35), rect)
            pygame.draw.rect(screen, item.color, rect, 3) 
            
            try:
                icon_surf = self.icon_font.render(item.icon, True, (255, 255, 255))
                screen.blit(icon_surf, icon_surf.get_rect(center=rect.center))
            except: pass

            pygame.draw.rect(screen, (255, 215, 0) if is_selected else (50, 50, 50), rect, 4 if is_selected else 2)

        screen.set_clip(None)

        total_rows = max(self.rows_visible, math.ceil(total_items / self.cols))
        track_w = 16
        track_x = start_x + self.cols * (slot_size + spacing) + 10
        scroll_track_rect = pygame.Rect(track_x, start_y, track_w, clip_h - spacing)
        
        pygame.draw.rect(screen, (20, 20, 25), scroll_track_rect)
        pygame.draw.rect(screen, (80, 80, 90), scroll_track_rect, 2) 
        
        if total_rows > self.rows_visible:
            thumb_height = max(30, (self.rows_visible / total_rows) * scroll_track_rect.height)
            thumb_y = start_y + (self.visual_scroll / max(1, total_rows - self.rows_visible)) * (scroll_track_rect.height - thumb_height)
            thumb_rect = pygame.Rect(scroll_track_rect.x + 3, thumb_y + 3, track_w - 6, thumb_height - 6)
            pygame.draw.rect(screen, (255, 100, 100), thumb_rect) 
        else:
            thumb_rect = pygame.Rect(scroll_track_rect.x + 3, start_y + 3, track_w - 6, scroll_track_rect.height - 6)
            pygame.draw.rect(screen, (50, 50, 55), thumb_rect) 

        # INFO READOUT
        if self.cursor_idx < total_items:
            sel_item = self.items[self.cursor_idx]
            info_txt = f"{sel_item.name} | {sel_item.rarity} | +{sel_item.effect_value} {sel_item.effect_stat}"
            screen.blit(self.title_font.render(info_txt, True, sel_item.color), (50, HEIGHT - 100))

        # --- QUANTITY SELECTOR UI ---
        if self.is_selecting_qty:
            cx, cy = WIDTH // 2, HEIGHT // 2
            box = pygame.Rect(0, 0, 400, 180)
            box.center = (cx, cy)
            pygame.draw.rect(screen, (40, 20, 20), box)
            pygame.draw.rect(screen, (255, 100, 100), box, 4)
            
            sel_item = self.items[self.cursor_idx]
            max_q = int(sel_item.max_stack)
            
            screen.blit(self.title_font.render(f"Spawn {sel_item.name}", True, (255, 255, 255)), self.title_font.render(f"Spawn {sel_item.name}", True, (255, 255, 255)).get_rect(center=(cx, cy - 40)))
            
            qty_txt = f"<   {self.spawn_qty}   >"
            screen.blit(self.title_font.render(qty_txt, True, (0, 255, 100)), self.title_font.render(qty_txt, True, (0, 255, 100)).get_rect(center=(cx, cy + 10)))
            
            max_txt = f"(Max: {max_q})"
            screen.blit(self.font.render(max_txt, True, (150, 150, 150)), self.font.render(max_txt, True, (150, 150, 150)).get_rect(center=(cx, cy + 40)))

        pygame.draw.rect(screen, (10, 10, 15), (0, HEIGHT - 40, WIDTH, 40))
        if self.is_selecting_qty:
            legend_text = "[Left/Right] +/- 1   |   [Up/Down] +/- 10   |   [A] Spawn   |   [B] Cancel"
        else:
            legend_text = "[Stick/D-Pad] Navigate   |   [A] Select Item   |   [B] Back"
        legend_surf = self.font.render(legend_text, True, (150, 150, 150))
        screen.blit(legend_surf, (WIDTH // 2 - legend_surf.get_width() // 2, HEIGHT - 28))