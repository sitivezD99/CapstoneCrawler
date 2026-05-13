# stats_equip_ui.py
import pygame
from pygame.math import Vector2
from settings import *

class StatsEquipUI:
    def __init__(self, player_attributes, player_equipment, player_inventory):
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        try: self.icon_font = pygame.font.SysFont(['segoe ui emoji', 'apple color emoji', 'noto color emoji'], 32)
        except: self.icon_font = self.font
        
        self.attributes, self.equipment, self.inventory = player_attributes, player_equipment, player_inventory
        self.slot_names = ["Head", "Necklace", "Chest", "MainHand", "OffHand", "Ring", "Legs", "Feet"]
        
        self.state = "DOLL" 
        self.cursor_idx, self.action_idx, self.selector_idx = 3, 0, 0
        self.action_options, self.selector_items = [], []
        self.sel_cols, self.sel_rows_visible = 5, 4
        self.stick_x_pressed, self.stick_y_pressed = False, False
        
        # AAA KINETICS
        self.actual_cursor_rect = pygame.Rect(0,0,0,0)
        self.drawer_offset = 450.0 

    def reset(self):
        self.cursor_idx, self.state = 3, "DOLL"

    def update(self, dt):
        """AAA Kinetics: Pop-out drawer and gliding Paper Doll cursor."""
        factor = min(dt * 15.0, 1.0)
        
        # Drawer sliding math
        target_drawer = 0.0 if self.state == "ITEM_SELECTOR" else 450.0
        self.drawer_offset += (target_drawer - self.drawer_offset) * factor
        
        # Gliding cursor for Paper Doll
        if self.state == "DOLL":
            rects = self._get_paper_doll_rects()
            t_rect = rects[self.slot_names[self.cursor_idx]]
            if self.actual_cursor_rect.width == 0:
                self.actual_cursor_rect = pygame.Rect(t_rect)
            else:
                self.actual_cursor_rect.x += (t_rect.x - self.actual_cursor_rect.x) * factor
                self.actual_cursor_rect.y += (t_rect.y - self.actual_cursor_rect.y) * factor
                self.actual_cursor_rect.w = t_rect.w
                self.actual_cursor_rect.h = t_rect.h

    def _get_valid_items(self, target_slot):
        return [s['item'] for s in self.inventory.slots if getattr(s['item'], 'equip_slot', None) == target_slot and not getattr(s['item'], 'is_equipped', False)]

    def _get_spatial_target(self, current_pos, nodes, direction_vec):
        best_idx, best_score = -1, float('inf')
        for i, target in enumerate(nodes):
            diff = target['pos'] - current_pos
            if diff.length() < 5.0: continue 
            dot = diff.normalize().dot(direction_vec)
            if dot > 0.4: 
                score = diff.length() * (1.0 + (1.0 - dot) * 2.0)
                if score < best_score: best_score, best_idx = score, i
        return best_idx

    def _wrap_left(self, idx, cols, max_idx):
        row_start = (idx // cols) * cols
        row_end = min(max_idx, row_start + cols - 1)
        return row_end if idx == row_start else idx - 1

    def _wrap_right(self, idx, cols, max_idx):
        row_start = (idx // cols) * cols
        row_end = min(max_idx, row_start + cols - 1)
        return row_start if idx == row_end else idx + 1

    def handle_input(self, event):
        is_back = (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]) or (event.type == pygame.JOYBUTTONDOWN and event.button == 1)
        if is_back:
            if self.state == "ITEM_SELECTOR": self.state = "ACTION_MENU"; return None
            elif self.state == "ACTION_MENU": self.state = "DOLL"; return None
            else: return "BACK"

        dx, dy, action = 0, 0, False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: dx = -1
            elif event.key == pygame.K_RIGHT: dx = 1
            elif event.key == pygame.K_UP: dy = -1
            elif event.key == pygame.K_DOWN: dy = 1
            elif event.key == pygame.K_RETURN: action = True
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
        elif event.type == pygame.JOYBUTTONDOWN and event.button == 0: action = True

        if self.state == "ITEM_SELECTOR":
            m_idx = len(self.selector_items) - 1
            if dx == -1: self.selector_idx = self._wrap_left(self.selector_idx, self.sel_cols, m_idx)
            elif dx == 1: self.selector_idx = self._wrap_right(self.selector_idx, self.sel_cols, m_idx)
            elif dy == -1: self.selector_idx = max(0, self.selector_idx - self.sel_cols)
            elif dy == 1: self.selector_idx = min(m_idx, self.selector_idx + self.sel_cols)
            if action and len(self.selector_items) > 0:
                self.state = "DOLL"
                return {"action": "EQUIP", "item": self.selector_items[self.selector_idx], "slot_name": self.slot_names[self.cursor_idx]}

        elif self.state == "ACTION_MENU":
            if dy == -1: self.action_idx = max(0, self.action_idx - 1)
            elif dy == 1: self.action_idx = min(len(self.action_options)-1, self.action_idx + 1)
            if action:
                act = self.action_options[self.action_idx]
                if act == "CANCEL": self.state = "DOLL"
                elif act == "UNEQUIP": self.state = "DOLL"; return {"action": "UNEQUIP", "slot_name": self.slot_names[self.cursor_idx]}
                elif act in ["EQUIP", "CHANGE"]:
                    self.selector_items = self._get_valid_items(self.slot_names[self.cursor_idx])
                    if len(self.selector_items) > 0: self.selector_idx, self.state = 0, "ITEM_SELECTOR"
                    else: self.state = "DOLL"

        elif self.state == "DOLL":
            if dx != 0 or dy != 0:
                rects = self._get_paper_doll_rects()
                nodes = [{'id': i, 'name': n, 'pos': Vector2(rects[n].center)} for i, n in enumerate(self.slot_names)]
                t_idx = self._get_spatial_target(nodes[self.cursor_idx]['pos'], nodes, Vector2(dx, dy).normalize() if dx and dy else Vector2(dx, dy))
                if t_idx != -1: self.cursor_idx = t_idx
            if action:
                self.action_options = ["CHANGE", "UNEQUIP", "CANCEL"] if self.equipment.slots.get(self.slot_names[self.cursor_idx]) else ["EQUIP", "CANCEL"]
                self.action_idx, self.state = 0, "ACTION_MENU"
        return None

    def _get_paper_doll_rects(self):
        cx, cy, sz = 350, 300, 70
        return {
            "Head": pygame.Rect(cx-sz//2, cy-180, sz, sz), "Necklace": pygame.Rect(cx+sz//2+10, cy-120, sz, sz),
            "Chest": pygame.Rect(cx-sz//2, cy-80, sz, sz), "MainHand": pygame.Rect(cx-sz*2, cy-30, sz, sz),
            "OffHand": pygame.Rect(cx+sz, cy-30, sz, sz), "Ring": pygame.Rect(cx-sz*2, cy+60, sz, sz),
            "Legs": pygame.Rect(cx-sz//2, cy+20, sz, sz), "Feet": pygame.Rect(cx-sz//2, cy+120, sz, sz)
        }

    def draw(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((15, 15, 20, 250)); screen.blit(overlay, (0,0))
        screen.blit(self.title_font.render("CHARACTER & EQUIPMENT", True, (255,215,0)), (50, 40))
        
        doll_rects = self._get_paper_doll_rects()
        pygame.draw.line(screen, (50,50,50), (350, 120), (350, 420), 4) 
        pygame.draw.line(screen, (50,50,50), (250, 270), (450, 270), 4) 
        
        for i, slot_name in enumerate(self.slot_names):
            r = doll_rects[slot_name]
            pygame.draw.rect(screen, (20, 20, 25), r)
            pygame.draw.rect(screen, (100, 100, 100), r, 2)
            item = self.equipment.slots.get(slot_name)
            if item:
                pygame.draw.rect(screen, item.color, r, 3)
                try: screen.blit(self.icon_font.render(item.icon, True, (255,255,255)), self.icon_font.render(item.icon, True, (255,255,255)).get_rect(center=r.center))
                except: pass
            else: screen.blit(self.font.render(slot_name[:4], True, (60,60,60)), self.font.render(slot_name[:4], True, (60,60,60)).get_rect(center=r.center))

        if self.state == "DOLL" or self.state == "ACTION_MENU":
            pygame.draw.rect(screen, (255, 215, 0), self.actual_cursor_rect, 4)

        if self.state == "ACTION_MENU":
            mx, my = self.actual_cursor_rect.right + 10, self.actual_cursor_rect.top
            pygame.draw.rect(screen, (10, 10, 15), (mx, my, 120, len(self.action_options)*30+10))
            pygame.draw.rect(screen, (255, 215, 0), (mx, my, 120, len(self.action_options)*30+10), 2)
            for i, opt in enumerate(self.action_options):
                if i == self.action_idx: pygame.draw.rect(screen, (255, 215, 0), (mx + 2, my + 5 + i*30, 116, 30))
                screen.blit(self.font.render(opt, True, (0,0,0) if i == self.action_idx else (255,255,255)), (mx + 10, my + 12 + i*30))

        # AAA Sliding Drawer Math
        r_rect = pygame.Rect(WIDTH - 450 + self.drawer_offset, 100, 400, 500)
        pygame.draw.rect(screen, (20, 20, 25), r_rect); pygame.draw.rect(screen, (80, 80, 90), r_rect, 2)

        if self.drawer_offset < 400: # Only draw internals if drawer is somewhat visible
            screen.blit(self.title_font.render("AVAILABLE GEAR", True, (255, 215, 0)), (r_rect.x + 30, 120))
            start_x, start_y, sz, sp = r_rect.x + 30, 160, 60, 10
            for i, item in enumerate(self.selector_items):
                r = pygame.Rect(start_x + (i%self.sel_cols)*(sz+sp), start_y + (i//self.sel_cols)*(sz+sp), sz, sz)
                is_sel = (i == self.selector_idx)
                pygame.draw.rect(screen, (60, 60, 70) if is_sel else (30, 30, 35), r)
                pygame.draw.rect(screen, item.color, r, 3)
                if is_sel: pygame.draw.rect(screen, (255, 215, 0), r, 5)
                try: screen.blit(self.icon_font.render(item.icon, True, (255,255,255)), self.icon_font.render(item.icon, True, (255,255,255)).get_rect(center=r.center))
                except: pass

            if len(self.selector_items) > 0:
                hov = self.selector_items[self.selector_idx]
                tt_rect = pygame.Rect(r_rect.x + 20, 380, 360, 200)
                pygame.draw.rect(screen, (15, 15, 15), tt_rect); pygame.draw.rect(screen, hov.color, tt_rect, 3)
                screen.blit(self.title_font.render(hov.name, True, hov.color), (tt_rect.x + 20, tt_rect.y + 20))
                screen.blit(self.font.render(f"Rarity: {hov.rarity}", True, (200,200,200)), (tt_rect.x + 20, tt_rect.y + 60))
                screen.blit(self.title_font.render(f"+{hov.effect_value} {hov.effect_stat}", True, (50, 255, 100)), (tt_rect.x + 20, tt_rect.y + 100))

        if self.state != "ITEM_SELECTOR":
            sx, sy = WIDTH - 420, 120
            screen.blit(self.title_font.render(f"LEVEL {self.attributes.level}", True, (255, 255, 255)), (sx, sy))
            screen.blit(self.font.render(f"EXP: {self.attributes.xp} / {self.attributes.xp_next}", True, (255, 215, 0)), (sx, sy+40))
            screen.blit(self.font.render(f"Max HP: {int(self.attributes.max_hp)}", True, (50, 255, 50)), (sx, sy+90))
            screen.blit(self.font.render(f"Max Mana: {int(self.attributes.max_mana)}", True, (50, 150, 255)), (sx + 200, sy+90))
            screen.blit(self.font.render(f"Base Damage: {int(self.attributes.damage)}", True, (255, 100, 100)), (sx, sy+130))
            screen.blit(self.font.render(f"Defense: {int(self.attributes.defense)}", True, (200, 200, 200)), (sx + 200, sy+130))
            screen.blit(self.title_font.render("CORE ATTRIBUTES", True, (150, 150, 150)), (sx, sy+190))
            screen.blit(self.font.render(f"Vigor: {self.attributes.base_vigor}", True, (255, 255, 255)), (sx, sy+230))
            screen.blit(self.font.render(f"Strength: {self.attributes.base_strength}", True, (255, 255, 255)), (sx + 200, sy+230))
            screen.blit(self.font.render(f"Agility: {self.attributes.base_agility}", True, (255, 255, 255)), (sx, sy+270))
            screen.blit(self.font.render(f"Intelligence: {self.attributes.base_intelligence}", True, (255, 255, 255)), (sx + 200, sy+270))

        pygame.draw.rect(screen, (10, 10, 15), (0, HEIGHT - 40, WIDTH, 40))
        screen.blit(self.font.render("[Stick/D-Pad] Spatial Navigate   |   [A] Action   |   [B] Back", True, (150, 150, 150)), (WIDTH // 2 - 250, HEIGHT - 28))