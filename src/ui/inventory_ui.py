# inventory_ui.py
import pygame
import math
import copy
from pygame.math import Vector2
from settings import *

class InventoryUI:
    def __init__(self, player_inventory): 
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        try: self.icon_font = pygame.font.SysFont(['segoe ui emoji', 'apple color emoji', 'noto color emoji'], 32)
        except: self.icon_font = self.font
        
        self.inventory = player_inventory
        self.categories = ["ALL", "WEAPON", "ARMOR", "GLYPH", "POTION", "MATERIAL"]
        self.cat_idx = 0
        self.cursor_idx = 0
        
        self.cols = 8 
        self.rows_visible = 6
        self.slots_per_page = self.cols * self.rows_visible
        
        self.show_action_menu = False
        self.action_options = []
        self.action_idx = 0
        self.active_slot = None
        
        # AAA CONFIRM STATE
        self.confirm_state = False
        self.confirm_idx = 1 # Default to NO
        
        self.l2_pressed = False
        self.r2_pressed = False
        self.stick_x_pressed = False
        self.stick_y_pressed = False
        
        self.visual_scroll = 0.0
        self.actual_cursor_rect = pygame.Rect(0,0,0,0)

    def reset(self):
        self.cat_idx = 0
        self.cursor_idx = 0
        self.show_action_menu = False
        self.confirm_state = False
        self.action_idx = 0
        self.active_slot = None

    def update(self, dt):
        factor = min(dt * 15.0, 1.0)
        target_scroll = (self.cursor_idx // self.cols) - (self.rows_visible - 1)
        if target_scroll < 0: target_scroll = 0
        self.visual_scroll += (target_scroll - self.visual_scroll) * factor
        
        start_x, start_y = 50, 140
        slot_size, spacing = 70, 15
        
        col = self.cursor_idx % self.cols
        row = self.cursor_idx // self.cols
        target_x = start_x + col * (slot_size + spacing)
        target_y = start_y + (row - self.visual_scroll) * (slot_size + spacing)
        
        if self.actual_cursor_rect.width == 0:
            self.actual_cursor_rect = pygame.Rect(target_x, target_y, slot_size, slot_size)
        else:
            self.actual_cursor_rect.x += (target_x - self.actual_cursor_rect.x) * factor
            self.actual_cursor_rect.y += (target_y - self.actual_cursor_rect.y) * factor
            self.actual_cursor_rect.w = slot_size
            self.actual_cursor_rect.h = slot_size

    def _populate_action_menu(self, slot):
        self.action_options = []
        item = slot['item']
        
        has_primary = False
        if item.is_consumable == "True": 
            self.action_options.append("USE"); has_primary = True
        elif getattr(item, 'equip_slot', None): 
            if getattr(item, 'is_equipped', False): self.action_options.append("UNEQUIP")
            else: self.action_options.append("EQUIP")
            has_primary = True
            
        if not has_primary: self.action_options.extend(["CANCEL", "DROP 1", "DROP ALL"])
        else: self.action_options.extend(["DROP 1", "DROP ALL", "CANCEL"])

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

    def handle_input(self, event):
        is_back = (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]) or \
                  (event.type == pygame.JOYBUTTONDOWN and event.button == 1)

        if is_back:
            if self.confirm_state: self.confirm_state = False; self.show_action_menu = True; return None
            if self.show_action_menu: self.show_action_menu = False; return None 
            else: return "BACK" 

        filtered = self.inventory.get_filtered_slots(self.categories[self.cat_idx])
        max_idx = max(0, len(filtered) - 1)
        if self.cursor_idx > max_idx: self.cursor_idx = max_idx

        dx, dy, action_pressed, tab_offset = 0, 0, False, 0

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: dx = -1
            elif event.key == pygame.K_RIGHT: dx = 1
            elif event.key == pygame.K_UP: dy = -1
            elif event.key == pygame.K_DOWN: dy = 1
            elif event.key == pygame.K_RETURN: action_pressed = True
            elif event.key == pygame.K_q: tab_offset = -1
            elif event.key == pygame.K_e: tab_offset = 1
        elif event.type == pygame.JOYHATMOTION:
            dx, dy = event.value[0], -event.value[1]
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value > 0.6 and not self.stick_x_pressed: dx = 1; self.stick_x_pressed = True
                elif event.value < -0.6 and not self.stick_x_pressed: dx = -1; self.stick_x_pressed = True
                elif abs(event.value) < 0.2: self.stick_x_pressed = False
            elif event.axis == 1:
                if event.value > 0.6 and not self.stick_y_pressed: dy = 1; self.stick_y_pressed = True
                elif event.value < -0.6 and not self.stick_y_pressed: dy = -1; self.stick_y_pressed = True
                elif abs(event.value) < 0.2: self.stick_y_pressed = False
            elif event.axis == 4 and not self.show_action_menu and not self.confirm_state:
                if event.value > 0.5 and not self.l2_pressed: tab_offset = -1; self.l2_pressed = True
                elif event.value < 0.2: self.l2_pressed = False
            elif event.axis == 5 and not self.show_action_menu and not self.confirm_state:
                if event.value > 0.5 and not self.r2_pressed: tab_offset = 1; self.r2_pressed = True
                elif event.value < 0.2: self.r2_pressed = False
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: action_pressed = True
            elif event.button == 4: tab_offset = -1
            elif event.button == 5: tab_offset = 1

        if tab_offset != 0 and not self.show_action_menu and not self.confirm_state:
            self.cat_idx = (self.cat_idx + tab_offset) % len(self.categories)
            self.cursor_idx = 0

        # --- AAA CONFIRM LOGIC ---
        if self.confirm_state:
            if dx == -1: self.confirm_idx = max(0, self.confirm_idx - 1)
            elif dx == 1: self.confirm_idx = min(1, self.confirm_idx + 1)
            if action_pressed:
                self.confirm_state = False
                if self.confirm_idx == 0: # YES
                    return {"action": "DROP_ALL", "slot": self.active_slot, "item": self.active_slot['item']}
                else:
                    self.show_action_menu = True
            return None

        if self.show_action_menu:
            if dy == -1: self.action_idx = max(0, self.action_idx - 1)
            elif dy == 1: self.action_idx = min(len(self.action_options) - 1, self.action_idx + 1)
            
            if action_pressed:
                act = self.action_options[self.action_idx]
                if act == "CANCEL": 
                    self.show_action_menu = False; return None
                elif act == "DROP ALL":
                    self.show_action_menu = False
                    self.confirm_state = True
                    self.confirm_idx = 1 # Safely default to NO
                    return None
                else:
                    self.show_action_menu = False
                    return {"action": act, "slot": self.active_slot, "item": self.active_slot['item']}
        else:
            if dy == -1: self.cursor_idx = max(0, self.cursor_idx - self.cols)
            elif dy == 1: self.cursor_idx = min(max_idx, self.cursor_idx + self.cols)
            elif dx == -1: self.cursor_idx = self._wrap_left(max_idx)
            elif dx == 1: self.cursor_idx = self._wrap_right(max_idx)
            
            if action_pressed and len(filtered) > 0:
                self.active_slot = filtered[self.cursor_idx]
                self._populate_action_menu(self.active_slot)
                self.action_idx, self.show_action_menu = 0, True
                    
        return None

    def draw(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 15, 20, 250))
        screen.blit(overlay, (0,0))
        screen.blit(self.title_font.render("ITEM INVENTORY", True, (255,255,255)), (50, 40))
        
        tab_x = 50
        for i, cat in enumerate(self.categories):
            col = (255, 215, 0) if i == self.cat_idx else (100, 100, 100)
            txt = self.font.render(cat, True, col)
            screen.blit(txt, (tab_x, 100))
            if i == self.cat_idx: pygame.draw.line(screen, col, (tab_x, 120), (tab_x + txt.get_width(), 120), 3)
            tab_x += txt.get_width() + 30

        filtered = self.inventory.get_filtered_slots(self.categories[self.cat_idx])
        start_x, start_y = 50, 140
        slot_size, spacing = 70, 15
        
        clip_h = self.rows_visible * (slot_size + spacing)
        screen.set_clip(pygame.Rect(40, 130, 800, clip_h))
        
        for i, slot in enumerate(filtered):
            col, row = i % self.cols, i // self.cols
            x = start_x + col * (slot_size + spacing)
            y = start_y + (row - self.visual_scroll) * (slot_size + spacing)
            
            if y > start_y + clip_h or y < start_y - slot_size: continue
            
            rect = pygame.Rect(x, y, slot_size, slot_size)
            pygame.draw.rect(screen, (30, 30, 35), rect)
            
            item = slot['item']
            pygame.draw.rect(screen, item.color, rect, 3) 
            try: screen.blit(self.icon_font.render(item.icon, True, (255, 255, 255)), self.icon_font.render(item.icon, True, (255, 255, 255)).get_rect(center=rect.center))
            except: pass
            if getattr(item, 'is_equipped', False):
                pygame.draw.rect(screen, (255,215,0), (x+2, y+2, 20, 20))
                screen.blit(self.font.render("E", True, (0,0,0)), (x+6, y+4))
            if slot['count'] > 1:
                screen.blit(self.font.render(str(slot['count']), True, (255,255,255)), (x + slot_size - 20, y + slot_size - 20))

        if len(filtered) > 0 and not self.show_action_menu and not self.confirm_state:
            pygame.draw.rect(screen, (255, 215, 0), self.actual_cursor_rect, 4)

        screen.set_clip(None)
        
        total_rows = max(self.rows_visible, math.ceil(len(filtered) / self.cols))
        track_x = start_x + self.cols * (slot_size + spacing) + 10
        s_rect = pygame.Rect(track_x, start_y, 16, clip_h - spacing)
        pygame.draw.rect(screen, (20, 20, 25), s_rect); pygame.draw.rect(screen, (80, 80, 90), s_rect, 2) 
        if total_rows > self.rows_visible:
            t_h = max(30, (self.rows_visible / total_rows) * s_rect.height)
            t_y = start_y + (self.visual_scroll / max(1, total_rows - self.rows_visible)) * (s_rect.height - t_h)
            pygame.draw.rect(screen, (255, 215, 0), pygame.Rect(s_rect.x + 3, t_y + 3, 10, t_h - 6)) 
        else:
            pygame.draw.rect(screen, (50, 50, 55), pygame.Rect(s_rect.x + 3, start_y + 3, 10, s_rect.height - 6))

        detail_rect = pygame.Rect(WIDTH - 400, 140, 350, 450)
        pygame.draw.rect(screen, (25, 25, 30), detail_rect)
        if len(filtered) > 0 and self.cursor_idx < len(filtered):
            sel = filtered[self.cursor_idx]['item']
            pygame.draw.rect(screen, sel.color, detail_rect, 5)
            screen.blit(self.title_font.render(sel.name, True, sel.color), (WIDTH - 380, 160))
            screen.blit(self.font.render(f"Category: {sel.category}", True, (200,200,200)), (WIDTH - 380, 200))
            eq_text = "EQUIPPED" if getattr(sel, 'is_equipped', False) else "IN BAG"
            screen.blit(self.font.render(f"Status: {eq_text}", True, (255,215,0) if getattr(sel, 'is_equipped', False) else (150,150,150)), (WIDTH - 200, 200))
            screen.blit(self.font.render(f"Rarity: {sel.rarity}", True, sel.color), (WIDTH - 380, 230))
            screen.blit(self.font.render(f"Effect: {sel.effect_stat}", True, (200,200,200)), (WIDTH - 380, 270))
            v_disp = f"+{sel.effect_value}" if sel.category != "Glyph" else f"+{int(float(sel.effect_value)*100)}%"
            screen.blit(self.font.render(f"Value: {v_disp}", True, (0,255,100)), (WIDTH - 380, 300))
            try: screen.blit(pygame.font.SysFont(['segoe ui emoji', 'apple color emoji'], 90).render(sel.icon, True, (255,255,255)), (WIDTH - 260, 370))
            except: pass
        else: pygame.draw.rect(screen, (100, 100, 100), detail_rect, 2)

        if self.show_action_menu:
            menu_w = 120
            menu_h = len(self.action_options) * 30 + 10
            mx, my = self.actual_cursor_rect.right + 10, self.actual_cursor_rect.top
            pygame.draw.rect(screen, (10, 10, 15), (mx, my, menu_w, menu_h))
            pygame.draw.rect(screen, (255, 215, 0), (mx, my, menu_w, menu_h), 2)
            for i, opt in enumerate(self.action_options):
                col = (0,0,0) if i == self.action_idx else (255,255,255)
                if i == self.action_idx: pygame.draw.rect(screen, (255, 215, 0), (mx + 2, my + 5 + i*30, menu_w - 4, 30))
                screen.blit(self.font.render(opt, True, col), (mx + 10, my + 12 + i*30))

        # --- DRAW CONFIRM BOX ---
        if self.confirm_state:
            cx, cy = WIDTH // 2, HEIGHT // 2
            box = pygame.Rect(0, 0, 400, 150)
            box.center = (cx, cy)
            pygame.draw.rect(screen, (40, 10, 10), box)
            pygame.draw.rect(screen, (255, 50, 50), box, 4)
            
            c_item = self.active_slot['item']
            c_count = self.active_slot['count']
            msg = f"Drop ALL {c_count}x {c_item.name}?"
            screen.blit(self.title_font.render(msg, True, (255,255,255)), self.title_font.render(msg, True, (255,255,255)).get_rect(center=(cx, cy - 20)))
            
            yes_col = (0,0,0) if self.confirm_idx == 0 else (255,255,255)
            yes_bg = (255,50,50) if self.confirm_idx == 0 else None
            if yes_bg: pygame.draw.rect(screen, yes_bg, (cx - 100, cy + 20, 80, 40))
            screen.blit(self.title_font.render("YES", True, yes_col), self.title_font.render("YES", True, yes_col).get_rect(center=(cx - 60, cy + 40)))

            no_col = (0,0,0) if self.confirm_idx == 1 else (255,255,255)
            no_bg = (100,100,100) if self.confirm_idx == 1 else None
            if no_bg: pygame.draw.rect(screen, no_bg, (cx + 20, cy + 20, 80, 40))
            screen.blit(self.title_font.render("NO", True, no_col), self.title_font.render("NO", True, no_col).get_rect(center=(cx + 60, cy + 40)))

        pygame.draw.rect(screen, (10, 10, 15), (0, HEIGHT - 40, WIDTH, 40))
        screen.blit(self.font.render("[Stick/D-Pad] Navigate   |   [A] Action   |   [B] Back", True, (150, 150, 150)), (WIDTH // 2 - 250, HEIGHT - 28))