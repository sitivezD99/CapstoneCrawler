# hex_system.py
import pygame
import math
import copy
import engine.item_database as item_database
from pygame.math import Vector2
from settings import *

def axial_to_pixel(q, r, size):
    x = size * math.sqrt(3) * (q + r / 2.0)
    y = size * (3.0 / 2.0) * r
    return Vector2(x, y)

class Socket:
    def __init__(self, q, r, x, y):
        self.q = q
        self.r = r
        self.base_pos = Vector2(x, y)
        self.linked_cores = [] 
        self.glyph = None
        
    @property
    def pos(self):
        return self.base_pos

class ForgeAnvil:
    def __init__(self, in_tier, out_tier, req_slots, crystal_cost):
        self.in_tier = in_tier
        self.out_tier = out_tier
        self.req_slots = req_slots
        self.crystal_cost = crystal_cost
        self.slots = []
        self.base_stat = None
        self.error_msg = ""
        self.error_timer = 0.0
        self.success_msg = ""
        self.success_timer = 0.0

    def update(self, dt):
        if self.error_timer > 0:
            self.error_timer -= dt
            if self.error_timer <= 0: self.error_msg = ""
        if self.success_timer > 0:
            self.success_timer -= dt
            if self.success_timer <= 0: self.success_msg = ""

class HexCoreUI:
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        try: 
            self.icon_font = pygame.font.SysFont(['segoe ui emoji', 'apple color emoji', 'noto color emoji'], 32)
            self.small_icon_font = pygame.font.SysFont(['segoe ui emoji', 'apple color emoji', 'noto color emoji'], 18)
        except: 
            self.icon_font = self.font
            self.small_icon_font = self.font
        
        self.sockets = {} 
        self.cores = []
        self.socket_list = []
        
        cx, cy = 850, HEIGHT // 2 - 40 
        local_hex_radius = 45 
        
        core_blueprints = [
            ("BASE COMBO", 0, 0, 1, "⚔️"),    
            ("HAMMER (X)", 2, 0, 5, "🔨"),     
            ("STUN (Y)", 2, 2, 10, "⚡"),       
            ("WHIRLWIND (B)", 0, 2, 15, "🌀")   
        ]
        
        cluster_center_pixel = axial_to_pixel(1, 1, local_hex_radius)
        offset_x, offset_y = cx - cluster_center_pixel.x, cy - cluster_center_pixel.y
        
        for name, q, r, lvl, icon in core_blueprints:
            pos = axial_to_pixel(q, r, local_hex_radius)
            self.cores.append({
                'name': name, 'q': q, 'r': r, 'lvl': lvl, 'icon': icon,
                'base_pos': Vector2(pos.x + offset_x, pos.y + offset_y)
            })
            
            neighbors = [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]
            for dq, dr in neighbors:
                sq, sr = q + dq, r + dr
                if (sq, sr) not in self.sockets:
                    spos = axial_to_pixel(sq, sr, local_hex_radius)
                    s = Socket(sq, sr, spos.x + offset_x, spos.y + offset_y)
                    self.sockets[(sq, sr)] = s
                    self.socket_list.append(s)
                if name not in self.sockets[(sq, sr)].linked_cores:
                    self.sockets[(sq, sr)].linked_cores.append(name)
        
        self.forge_btn_pos = Vector2(WIDTH // 2, HEIGHT - 50)
        self.skill_stats = {}
        self.recalculate_stats()

        self.active_pane = "GRID"
        self.grid_idx, self.bag_idx = 0, 0
        self.bag_cols, self.bag_rows_visible = 5, 3
        
        self.held_glyph = None 
        self.target_socket_idx = -1 
        self.pulse_timer = 0.0 # NEW: Visual juice timer
        
        self.stick_x_pressed, self.stick_y_pressed = False, False
        self.visual_bag_scroll = 0.0
        self.screen_y_level, self.camera_y_offset = 0, 0.0 
        
        self.anvils = [
            ForgeAnvil("Rare", "Epic", 2, 2),
            ForgeAnvil("Epic", "Mythic", 3, 3),
            ForgeAnvil("Mythic", "Legendary", 5, 5)
        ]

    def update(self, dt):
        t_scroll = (self.bag_idx // self.bag_cols) - (self.bag_rows_visible - 1)
        if t_scroll < 0: t_scroll = 0
        self.visual_bag_scroll += (t_scroll - self.visual_bag_scroll) * min(dt * 15.0, 1.0)
        target_y = -(self.screen_y_level * HEIGHT)
        self.camera_y_offset += (target_y - self.camera_y_offset) * min(dt * 10.0, 1.0)
        
        if self.pulse_timer > 0:
            self.pulse_timer -= dt
            
        for anvil in self.anvils: anvil.update(dt)

    def recalculate_stats(self):
        self.skill_stats = {n: {'Force': 0.0, 'Reach': 0.0, 'Impact': 0.0, 'Haste': 0.0, 'Vampire': 0.0} for n in ["BASE COMBO", "HAMMER (X)", "STUN (Y)", "WHIRLWIND (B)"]}
        for (q, r), socket in self.sockets.items():
            if socket.glyph:
                g, res = socket.glyph, 0.0
                for dq, dr in [(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)]:
                    if (q+dq, r+dr) in self.sockets and self.sockets[(q+dq, r+dr)].glyph:
                        n_g = self.sockets[(q+dq, r+dr)].glyph
                        if getattr(n_g, 'effect_stat', None) == getattr(g, 'effect_stat', None) and getattr(n_g, 'rarity', None) == getattr(g, 'rarity', None): res += 0.25 
                final_val = float(g.effect_value) * (1.0 + res)
                for core in socket.linked_cores: self.skill_stats[core][g.effect_stat] += final_val

    def is_socket_unlocked(self, socket, current_level):
        for c_name in socket.linked_cores:
            c = next((c for c in self.cores if c['name'] == c_name), None)
            if c and current_level >= c['lvl']: return True
        return False

    def _get_spatial_target_hex(self, current_pos, direction_vec, current_level):
        best_idx, best_score = -1, float('inf')
        for i, target in enumerate(self.socket_list):
            if not self.is_socket_unlocked(target, current_level): continue
            diff = target.pos - current_pos
            if diff.length() < 5.0: continue 
            dot = diff.normalize().dot(direction_vec)
            if dot > 0.5: 
                score = diff.length() * (1.0 + (1.0 - dot) * 2.0)
                if score < best_score: best_score, best_idx = score, i
        
        if not self.held_glyph:
            diff = self.forge_btn_pos - current_pos
            if diff.length() >= 5.0:
                dot = diff.normalize().dot(direction_vec)
                if dot > 0.5:
                    score = diff.length() * (1.0 + (1.0 - dot) * 2.0)
                    if score < best_score: best_score, best_idx = score, 999 
        return best_idx

    def _return_all_to_bag(self, player_inventory):
        for anvil in self.anvils:
            for g in anvil.slots: player_inventory.add_item(g)
            anvil.slots, anvil.base_stat = [], None

    def _get_official_db_item(self, rarity, effect_stat):
        for item in item_database.GLOBAL_DB.items.values():
            if hasattr(item, 'rarity') and hasattr(item, 'effect_stat'):
                if item.rarity == rarity and item.effect_stat == effect_stat:
                    return copy.copy(item)
        return None

    def handle_input(self, event, player_inventory, current_level):
        is_back = (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]) or (event.type == pygame.JOYBUTTONDOWN and event.button == 1)
        
        if is_back:
            if self.screen_y_level == 1:
                self.screen_y_level, self.grid_idx = 0, 999
                self._return_all_to_bag(player_inventory)
                return None
            else:
                if self.held_glyph: 
                    player_inventory.add_item(self.held_glyph)
                    self.held_glyph, self.target_socket_idx = None, -1
                    return None
                elif self.active_pane == "BAG": 
                    self.active_pane, self.target_socket_idx = "GRID", -1
                    return None
                else: return "BACK" 

        glyph_slots = player_inventory.get_filtered_slots("GLYPH")
        max_bag = max(0, len(glyph_slots) - 1)

        dx, dy, action, cancel_action = 0, 0, False, False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: dx = -1
            elif event.key == pygame.K_RIGHT: dx = 1
            elif event.key == pygame.K_UP: dy = -1
            elif event.key == pygame.K_DOWN: dy = 1
            elif event.key == pygame.K_RETURN: action = True
            elif event.key == pygame.K_y: cancel_action = True
        elif event.type == pygame.JOYHATMOTION: dx, dy = event.value[0], -event.value[1] 
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value > 0.6 and not self.stick_x_pressed: dx, self.stick_x_pressed = 1, True
                elif event.value < -0.6 and not self.stick_x_pressed: dx, self.stick_x_pressed = -1, True
                elif abs(event.value) < 0.2: self.stick_x_pressed = False
            elif event.axis == 1:
                if event.value > 0.6 and not self.stick_y_pressed: dy, self.stick_y_pressed = 1, True
                elif event.value < -0.6 and not self.stick_y_pressed: dy, self.stick_y_pressed = -1, True
                elif abs(event.value) < 0.2: self.stick_y_pressed = False
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: action = True
            elif event.button == 3: cancel_action = True 

        if dx == 0 and dy == 0 and not action and not cancel_action: return None

        # --- FORGE ROOM ---
        if self.screen_y_level == 1:
            if dx != 0 or dy != 0:
                if dx == 1: self.bag_idx = min(max_bag, self.bag_idx + 1)
                elif dx == -1: self.bag_idx = max(0, self.bag_idx - 1)
                elif dy == -1: 
                    if self.bag_idx < self.bag_cols:
                        self.screen_y_level, self.grid_idx = 0, 999
                        self._return_all_to_bag(player_inventory)
                    else: self.bag_idx = max(0, self.bag_idx - self.bag_cols)
                elif dy == 1: self.bag_idx = min(max_bag, self.bag_idx + self.bag_cols)
            
            active_anvil = next((a for a in self.anvils if len(a.slots) > 0), None)
            hovered_item = glyph_slots[self.bag_idx]['item'] if self.bag_idx < len(glyph_slots) else None
            target_anvil = active_anvil if active_anvil else (next((a for a in self.anvils if hovered_item and a.in_tier == hovered_item.rarity), None))

            if cancel_action and active_anvil:
                for g in active_anvil.slots: player_inventory.add_item(g)
                active_anvil.slots, active_anvil.base_stat = [], None
                return None

            if action and target_anvil:
                if len(target_anvil.slots) == target_anvil.req_slots:
                    crystals = player_inventory.count_item("mat_magic_crystal")
                    if crystals >= target_anvil.crystal_cost:
                        player_inventory.remove_item_by_id("mat_magic_crystal", target_anvil.crystal_cost)
                        off_item = self._get_official_db_item(target_anvil.out_tier, target_anvil.base_stat)
                        if off_item: player_inventory.add_item(off_item)
                        target_anvil.slots, target_anvil.base_stat = [], None
                        target_anvil.success_msg, target_anvil.success_timer = f"Forged {target_anvil.out_tier}!", 2.0
                    else: target_anvil.error_msg, target_anvil.error_timer = f"Need {target_anvil.crystal_cost} Crystals!", 2.0
                elif hovered_item and hovered_item.rarity == target_anvil.in_tier:
                    if len(target_anvil.slots) == 0 or target_anvil.base_stat == hovered_item.effect_stat:
                        target_anvil.base_stat = hovered_item.effect_stat
                        target_anvil.slots.append(copy.copy(hovered_item))
                        player_inventory.remove_slot_item(glyph_slots[self.bag_idx], 1)
                    else: target_anvil.error_msg, target_anvil.error_timer = "Stat Mismatch!", 2.0
            return None

        # --- GRID ROOM ---
        if self.screen_y_level == 0:
            if dx != 0 or dy != 0:
                if self.active_pane == "BAG":
                    if dx == 1 and (self.bag_idx + 1) % self.bag_cols == 0: self.active_pane, self.target_socket_idx = "GRID", -1
                    elif dx == 1: self.bag_idx = min(max_bag, self.bag_idx + 1)
                    elif dx == -1: self.bag_idx = max(0, self.bag_idx - 1)
                    elif dy == -1: self.bag_idx = max(0, self.bag_idx - self.bag_cols)
                    elif dy == 1: self.bag_idx = min(max_bag, self.bag_idx + self.bag_cols)
                elif self.active_pane == "GRID":
                    curr_pos = self.forge_btn_pos if self.grid_idx == 999 else self.socket_list[self.grid_idx].pos
                    dir_vec = Vector2(dx, dy).normalize() if dx or dy else Vector2(0)
                    target = self._get_spatial_target_hex(curr_pos, dir_vec, current_level)
                    
                    if dy == 1 and self.grid_idx == 999: self.screen_y_level = 1
                    elif self.held_glyph and target == 999: pass 
                    elif target != -1: self.grid_idx = target
                    elif dx == -1: 
                        if self.held_glyph: player_inventory.add_item(self.held_glyph); self.held_glyph = None
                        self.active_pane = "BAG"

            if action:
                if self.active_pane == "BAG":
                    if len(glyph_slots) > 0:
                        slot = glyph_slots[self.bag_idx]
                        if self.target_socket_idx != -1:
                            ts = self.socket_list[self.target_socket_idx]
                            old_g = ts.glyph
                            ts.glyph = copy.copy(slot['item'])
                            player_inventory.remove_item_by_id(slot['item'].item_id, 1)
                            if old_g: player_inventory.add_item(old_g)
                            self.target_socket_idx, self.active_pane = -1, "GRID"
                            self.grid_idx = next((i for i, s in enumerate(self.socket_list) if s == ts), 0)
                            self.recalculate_stats()
                        elif not self.held_glyph: 
                            self.held_glyph = copy.copy(slot['item'])
                            player_inventory.remove_item_by_id(slot['item'].item_id, 1) 
                            if self.grid_idx == 999: 
                                self.grid_idx = 0
                                self.pulse_timer = 1.5 # Trigger juice!
                            self.active_pane = "GRID" 
                elif self.active_pane == "GRID":
                    if self.grid_idx == 999: self.screen_y_level = 1
                    else:
                        ts = self.socket_list[self.grid_idx]
                        if self.is_socket_unlocked(ts, current_level):
                            if self.held_glyph: 
                                old_g = ts.glyph
                                ts.glyph, self.held_glyph = self.held_glyph, old_g 
                                self.recalculate_stats()
                            else:
                                if ts.glyph: self.held_glyph, ts.glyph = ts.glyph, None; self.recalculate_stats()
                                else: self.target_socket_idx, self.active_pane, self.bag_idx = self.grid_idx, "BAG", 0
        return None

    def _draw_poly(self, screen, x, y, radius, color, width=0):
        pts = [(x + radius * math.cos(math.radians(60 * i - 30)), y + radius * math.sin(math.radians(60 * i - 30))) for i in range(6)]
        pygame.draw.polygon(screen, color, pts, width)

    def draw(self, screen, current_level, player_inventory):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill(HEX_MENU_COLOR); screen.blit(overlay, (0,0))
        yo = self.camera_y_offset
        glyph_slots = player_inventory.get_filtered_slots("GLYPH")
        if len(glyph_slots) > 0: self.bag_idx = max(0, min(self.bag_idx, len(glyph_slots)-1))

        pw = 420
        pygame.draw.rect(screen, (20, 20, 25), (0, yo, pw, HEIGHT))
        pygame.draw.line(screen, (80, 80, 80), (pw, yo), (pw, yo + HEIGHT), 3)
        pygame.draw.line(screen, (50, 50, 50), (0, yo + 360), (pw, yo + 360), 3) 
        is_bag_active = (self.active_pane == "BAG" and self.screen_y_level == 0)
        pygame.draw.rect(screen, (255, 215, 0) if is_bag_active else (60, 60, 60), (0, yo, pw, 360), 3)
        screen.blit(self.title_font.render("AVAILABLE GLYPHS", True, (255,255,255)), (20, yo + 20))
        
        if glyph_slots:
            sx, sy, sz, sp = 20, 60, 65, 12
            screen.set_clip(pygame.Rect(10, yo + 50, 400, self.bag_rows_visible*(sz+sp)+10))
            for i, slot in enumerate(glyph_slots):
                col, row = i % self.bag_cols, i // self.bag_cols
                x, y = sx + col * (sz + sp), sy + (row - self.visual_bag_scroll) * (sz + sp) + yo
                if y > sy + yo + (self.bag_rows_visible*(sz+sp)) or y < sy + yo - sz: continue
                rect = pygame.Rect(x, y, sz, sz)
                pygame.draw.rect(screen, (60, 60, 70) if (is_bag_active and i == self.bag_idx) else (30, 30, 35), rect)
                pygame.draw.rect(screen, slot['item'].color, rect, 3)
                if is_bag_active and i == self.bag_idx: pygame.draw.rect(screen, (255, 215, 0), rect, 5)
                try: screen.blit(self.icon_font.render(slot['item'].icon, True, (255, 255, 255)), self.icon_font.render(slot['item'].icon, True, (255, 255, 255)).get_rect(center=rect.center))
                except: pass
                if slot['count'] > 1: screen.blit(self.font.render(str(slot['count']), True, (255,255,255)), (x + sz - 20, y + sz - 20))
            screen.set_clip(None)

        screen.blit(self.title_font.render("HEX-CORE TELEMETRY", True, (255,255,255)), (20, yo + 380))
        cur_y = yo + 420
        for core in self.cores:
            cn = core['name']
            if current_level >= core['lvl']:
                screen.blit(self.font.render(f"[{cn}]", True, (255,215,0)), (20, cur_y)); cur_y += 25; has_s = False
                for k, v in self.skill_stats[cn].items():
                    if v > 0: screen.blit(self.font.render(f" + {k}: +{int(v*100)}%", True, (0, 255, 100)), (30, cur_y)); cur_y += 20; has_s = True
                if not has_s: screen.blit(self.font.render("   Empty Sockets", True, (100, 100, 100)), (30, cur_y)); cur_y += 20
                cur_y += 10
            else: screen.blit(self.font.render(f"[{cn}] (Lvl {core['lvl']})", True, (100,100,100)), (20, cur_y)); cur_y += 30

        for i, s in enumerate(self.socket_list):
            sx, sy_soc = s.pos.x, s.pos.y + yo
            if self.is_socket_unlocked(s, current_level):
                self._draw_poly(screen, sx, sy_soc, 43, s.glyph.color if s.glyph else (15,15,15))
                if (self.active_pane == "GRID" and i == self.grid_idx and self.screen_y_level == 0) or (i == self.target_socket_idx):
                    self._draw_poly(screen, sx, sy_soc, 47, (255, 215, 0), 4)
                else: self._draw_poly(screen, sx, sy_soc, 43, (60,60,60), 2)
                
                # JUMP PULSE JUICE
                if i == 0 and self.pulse_timer > 0:
                    alpha = int(abs(math.sin(pygame.time.get_ticks() * 0.01)) * 255)
                    self._draw_poly(screen, sx, sy_soc, 55, (255, 255, 255, alpha), 3)

                if s.glyph:
                    try: screen.blit(self.icon_font.render(s.glyph.icon, True, (255, 255, 255)), self.icon_font.render(s.glyph.icon, True, (255, 255, 255)).get_rect(center=(sx, sy_soc)))
                    except: pass
            else:
                self._draw_poly(screen, sx, sy_soc, 43, (5, 5, 5))
                self._draw_poly(screen, sx, sy_soc, 43, (40, 0, 0), 2)
            
        for c in self.cores:
            is_u, cx, cy_c = current_level >= c['lvl'], c['base_pos'].x, c['base_pos'].y + yo
            self._draw_poly(screen, cx, cy_c, 45, COLOR_MAIN_HEX if is_u else (0,0,0))
            self._draw_poly(screen, cx, cy_c, 45, (255, 255, 255) if is_u else COLOR_LOCKED, 3)
            if is_u:
                try: screen.blit(self.icon_font.render(c['icon'], True, (255,255,255)), self.icon_font.render(c['icon'], True, (255,255,255)).get_rect(center=(cx, cy_c - 5)))
                except: pass

        bx, by = self.forge_btn_pos.x, self.forge_btn_pos.y + yo
        is_sel = (self.active_pane == "GRID" and self.grid_idx == 999 and self.screen_y_level == 0)
        btn_s = self.title_font.render("THE ARCANE FORGE", True, (255, 255, 255) if is_sel else (150, 150, 150))
        br = btn_s.get_rect(center=(bx, by))
        if is_sel:
            pygame.draw.rect(screen, (50, 50, 60), br.inflate(40, 20), border_radius=10)
            pygame.draw.rect(screen, (255, 215, 0), br.inflate(40, 20), 2, border_radius=10)
        screen.blit(btn_s, br)

        if self.held_glyph and self.screen_y_level == 0:
            v_tx, v_ty = (self.socket_list[self.grid_idx].pos.x if self.grid_idx != 999 else bx), (self.socket_list[self.grid_idx].pos.y + yo if self.grid_idx != 999 else by)
            self._draw_poly(screen, v_tx, v_ty, 50, self.held_glyph.color)
            self._draw_poly(screen, v_tx, v_ty, 50, (255,255,255), 2)
            try: screen.blit(self.icon_font.render(self.held_glyph.icon, True, (255, 255, 255)), self.icon_font.render(self.held_glyph.icon, True, (255, 255, 255)).get_rect(center=(v_tx, v_ty)))
            except: pass

        fy = HEIGHT + yo
        if fy < HEIGHT and fy + HEIGHT > 0: 
            lw = WIDTH - 420
            pygame.draw.rect(screen, (15, 10, 10), (0, fy, lw, HEIGHT))
            pygame.draw.line(screen, (255, 100, 50), (lw, fy), (lw, fy + HEIGHT), 3)
            pygame.draw.rect(screen, (20, 20, 25), (lw, fy, 420, HEIGHT))
            pygame.draw.rect(screen, (255, 215, 0) if self.screen_y_level == 1 else (60, 60, 60), (lw, fy, 420, HEIGHT), 3)
            screen.blit(self.title_font.render(f"Magic Crystals: {player_inventory.count_item('mat_magic_crystal')}", True, (0, 255, 255)), (40, fy + 30))
            aa = next((a for a in self.anvils if len(a.slots) > 0), None)
            hi = glyph_slots[self.bag_idx]['item'] if (self.bag_idx < len(glyph_slots) and self.screen_y_level == 1) else None
            for i, anvil in enumerate(self.anvils):
                ay = fy + 130 + (i * 180)
                is_lit = (aa == anvil) or (not aa and hi and hi.rarity == anvil.in_tier)
                box = pygame.Rect(40, ay - 40, lw - 80, 120)
                pygame.draw.rect(screen, (30, 20, 20) if is_lit else (20, 10, 10), box, border_radius=10)
                pygame.draw.rect(screen, (255, 215, 0) if is_lit else (80, 40, 40), box, 3, border_radius=10)
                screen.blit(self.title_font.render(f"{anvil.in_tier} -> {anvil.out_tier}", True, (200, 200, 200)), (60, ay - 25))
                screen.blit(self.font.render(f"Cost: {anvil.crystal_cost} Crystals", True, (0, 255, 255)), (60, ay + 15))
                if anvil.error_timer > 0: screen.blit(self.font.render(anvil.error_msg, True, (255, 50, 50)), (60, ay + 45))
                elif anvil.success_timer > 0: screen.blit(self.font.render(anvil.success_msg, True, (50, 255, 50)), (60, ay + 45))
                for s in range(anvil.req_slots):
                    sx, sy = 220 + (s * 55), ay + 20
                    pygame.draw.circle(screen, (10, 10, 15), (sx, sy), 25)
                    pygame.draw.circle(screen, (100, 100, 100), (sx, sy), 25, 2)
                    if s < len(anvil.slots):
                        pygame.draw.circle(screen, anvil.slots[s].color, (sx, sy), 22, 3)
                        try: screen.blit(self.icon_font.render(anvil.slots[s].icon, True, (255, 255, 255)), self.icon_font.render(anvil.slots[s].icon, True, (255, 255, 255)).get_rect(center=(sx, sy)))
                        except: pass
                screen.blit(self.title_font.render("->", True, (150, 150, 150)), (220 + (anvil.req_slots*55) + 10, ay + 5))
                oc = COLOR_EPIC if anvil.out_tier == "Epic" else (COLOR_MYTHIC if anvil.out_tier == "Mythic" else COLOR_LEGENDARY)
                screen.blit(self.title_font.render(f"{anvil.out_tier}", True, oc), (220 + (anvil.req_slots*55) + 50, ay + 5))
                if len(anvil.slots) == anvil.req_slots:
                    mr = pygame.Rect(220 + (anvil.req_slots*55) + 170, ay, 120, 30)
                    pygame.draw.rect(screen, (0, 255, 100), mr, border_radius=5)
                    screen.blit(self.font.render("[A] MERGE", True, (0,0,0)), (mr.x + 15, ay + 6))
            screen.blit(self.title_font.render("AVAILABLE GLYPHS", True, (255,255,255)), (lw + 20, fy + 20))
            if glyph_slots:
                stx, sty, sz, sp = lw + 20, 60, 65, 12
                screen.set_clip(pygame.Rect(lw + 10, fy + 50, 400, self.bag_rows_visible * (sz + sp) + 10))
                for i, slot in enumerate(glyph_slots):
                    c, r = i % self.bag_cols, i // self.bag_cols
                    x, y = stx + c * (sz+sp), sty + (r - self.visual_bag_scroll) * (sz+sp) + fy
                    if y > sty + fy + (self.bag_rows_visible*(sz+sp)) or y < sty + fy - sz: continue
                    rect = pygame.Rect(x, y, sz, sz)
                    pygame.draw.rect(screen, (60, 60, 70) if i == self.bag_idx else (30, 30, 35), rect)
                    pygame.draw.rect(screen, slot['item'].color, rect, 3)
                    if i == self.bag_idx: pygame.draw.rect(screen, (255, 215, 0), rect, 5)
                    try: screen.blit(self.icon_font.render(slot['item'].icon, True, (255, 255, 255)), self.icon_font.render(slot['item'].icon, True, (255, 255, 255)).get_rect(center=rect.center))
                    except: pass
                    if slot['count'] > 1: screen.blit(self.font.render(str(slot['count']), True, (255,255,255)), (x + sz - 20, y + sz - 20))
                screen.set_clip(None)

        pygame.draw.rect(screen, (10, 10, 15), (0, HEIGHT - 40, WIDTH, 40))
        if self.target_socket_idx != -1: legend = "[Stick/D-Pad] Choose Glyph   |   [A] Confirm Placement   |   [B] Cancel Jump"
        elif self.screen_y_level == 1: legend = "[Stick/D-Pad] Navigate Bag (Up to Exit)   |   [A] Fill / Merge   |   [Y] Recall"
        else: legend = "[Stick/D-Pad] Navigate   |   [A] Drag/Swap   |   [B] Return to Bag"
        legend_surf = self.font.render(legend, True, (150, 150, 150))
        screen.blit(legend_surf, (WIDTH // 2 - legend_surf.get_width() // 2, HEIGHT - 28))