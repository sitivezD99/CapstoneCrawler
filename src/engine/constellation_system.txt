# constellation_system.py
import pygame
import math
import os
import copy
import engine.item_database as item_database
from pygame.math import Vector2
from settings import *

class StarNode:
    def __init__(self, node_id, name, x, y, tier, cost, stat_type, stat_value, reqs, desc):
        self.node_id = node_id
        self.name = name
        self.pos = Vector2(float(x), float(y)) 
        self.tier = tier 
        self.cost = int(cost)
        self.stat_type = stat_type 
        self.stat_value = float(stat_value)
        self.reqs = [r.strip() for r in reqs.split("|") if r.strip()] if reqs else []
        self.desc = desc
        self.is_unlocked = False

class ConstellationRegistry:
    HEADERS = ['ID', 'Name', 'X', 'Y', 'Tier', 'Cost', 'Stat_Type', 'Stat_Value', 'Reqs', 'Description']
    
    def __init__(self):
        self.nodes = {}
        self._initialize_base_tree()

    def _initialize_base_tree(self):
        cx, cy = WIDTH//2, HEIGHT//2
        # AAA HARD CAP DESIGN: 
        # Minor = 3, Major = 5, Keystone = 8
        # Total cost of tree is ~152. Player is permanently capped at 100 via the Arcane Tube.
        raw_nodes = [
            # ROOT
            StarNode("st_root", "The Awakening", cx, cy, "Major", 0, "Max_HP", 50, "", "The journey begins."),

            # --- VIGOR CLUSTER (Top Left - Sprawling Web) ---
            StarNode("st_v_1", "Bear's Blood", cx - 120, cy - 80, "Minor", 3, "Vigor", 2, "st_root", "Increases base vitality."),
            StarNode("st_v_1a", "Toughness", cx - 80, cy - 160, "Minor", 3, "Defense", 3, "st_v_1", "Armor +"),
            StarNode("st_v_1b", "Regrowth", cx - 180, cy - 200, "Minor", 3, "Vigor", 2, "st_v_1a", "Health +"),
            StarNode("st_v_1c", "Thick Skull", cx - 40, cy - 240, "Minor", 3, "Defense", 5, "st_v_1a", "Armor ++"),
            StarNode("st_v_2", "Iron Hide", cx - 260, cy - 120, "Minor", 3, "Vigor", 3, "st_v_1", "Thickens the skin."),
            StarNode("st_v_3", "Titan's Core", cx - 380, cy - 180, "Major", 5, "Max_HP", 100, "st_v_2|st_v_1b", "Massive health increase."),
            StarNode("st_v_3a", "Goliath", cx - 440, cy - 100, "Major", 5, "Defense", 15, "st_v_3", "Massive armor increase."),
            StarNode("st_v_key", "Juggernaut", cx - 540, cy - 220, "Keystone", 8, "Impact", 0.50, "st_v_3", "Knockback pushes enemies 50% further."),

            # --- STRENGTH CLUSTER (Top Right - Linear Sharp) ---
            StarNode("st_s_1", "Raven's Eye", cx + 140, cy - 70, "Minor", 3, "Strength", 2, "st_root", "Increases base muscle."),
            StarNode("st_s_1a", "Heavy Hand", cx + 220, cy - 30, "Minor", 3, "Base_Damage", 5, "st_s_1", "Flat damage +"),
            StarNode("st_s_1b", "Cruelty", cx + 300, cy - 40, "Minor", 3, "Strength", 2, "st_s_1a", "Muscle +"),
            StarNode("st_s_1c", "Savage", cx + 380, cy - 20, "Minor", 3, "Base_Damage", 8, "st_s_1b", "Flat damage ++"),
            StarNode("st_s_2", "Sharpened Blade", cx + 280, cy - 140, "Minor", 3, "Strength", 3, "st_s_1", "Hones combat power."),
            StarNode("st_s_3", "Lethal Strike", cx + 420, cy - 190, "Major", 5, "Base_Damage", 15, "st_s_2", "Massive damage increase."),
            StarNode("st_s_3a", "Executioner", cx + 520, cy - 150, "Major", 5, "Strength", 10, "st_s_3|st_s_1c", "Massive power increase."),
            StarNode("st_s_key", "Bloodthirst", cx + 600, cy - 260, "Keystone", 8, "Vampire", 0.05, "st_s_3", "Global Lifesteal."),

            # --- INT CLUSTER (Bottom Right - Circular Scatter) ---
            StarNode("st_i_1", "Mind's Spark", cx + 110, cy + 110, "Minor", 3, "Intelligence", 2, "st_root", "Increases arcane flow."),
            StarNode("st_i_1a", "Clear Cast", cx + 80, cy + 200, "Minor", 3, "Max_Mana", 15, "st_i_1", "Mana +"),
            StarNode("st_i_1b", "Focus", cx + 200, cy + 240, "Minor", 3, "Intelligence", 2, "st_i_1a", "Int +"),
            StarNode("st_i_1c", "Meditation", cx + 120, cy + 300, "Minor", 3, "Max_Mana", 20, "st_i_1b", "Mana ++"),
            StarNode("st_i_2", "Deep Well", cx + 260, cy + 130, "Minor", 3, "Intelligence", 3, "st_i_1", "Expands mana reserves."),
            StarNode("st_i_3", "Arcane Core", cx + 380, cy + 180, "Major", 5, "Max_Mana", 50, "st_i_2|st_i_1b", "Massive mana increase."),
            StarNode("st_i_3a", "Omnipotence", cx + 400, cy + 300, "Major", 5, "Intelligence", 10, "st_i_3|st_i_1c", "Massive arcane flow."),
            StarNode("st_i_key", "Archmage", cx + 500, cy + 220, "Keystone", 8, "Force", 0.20, "st_i_3", "Spells hit with 20% more Force."),

            # --- AGI CLUSTER (Bottom Left - Zig Zag) ---
            StarNode("st_a_1", "Wolf's Pace", cx - 130, cy + 90, "Minor", 3, "Haste", 0.05, "st_root", "Increases combat speed."),
            StarNode("st_a_1a", "Swift", cx - 250, cy + 60, "Minor", 3, "Haste", 0.02, "st_a_1", "Speed +"),
            StarNode("st_a_1b", "Evasion", cx - 320, cy + 100, "Minor", 3, "Defense", 4, "st_a_1a", "Dodge +"),
            StarNode("st_a_1c", "Ghost Step", cx - 400, cy + 80, "Minor", 3, "Haste", 0.03, "st_a_1b", "Speed ++"),
            StarNode("st_a_2", "Feral Lunge", cx - 220, cy + 170, "Minor", 3, "Reach", 0.10, "st_a_1", "Increases attack area size."),
            StarNode("st_a_3", "Thrill of Hunt", cx - 350, cy + 220, "Major", 5, "Haste", 0.10, "st_a_2", "Massive speed increase."),
            StarNode("st_a_3a", "Windwalker", cx - 460, cy + 180, "Major", 5, "Reach", 0.20, "st_a_3|st_a_1c", "Massive area increase."),
            StarNode("st_a_key", "Frenzy", cx - 500, cy + 300, "Keystone", 8, "Haste", 0.20, "st_a_3", "Attack at blinding speeds."),

            # --- OUTER BRIDGES (Connecting the Web) ---
            StarNode("st_bridge_vs", "Warlord", cx, cy - 300, "Major", 5, "Defense", 10, "st_v_1c|st_s_2", "Armor and Power."),
            StarNode("st_bridge_ia", "Shadow", cx, cy + 380, "Major", 5, "Haste", 0.15, "st_i_1c|st_a_key", "Magic and Speed."),
            StarNode("st_bridge_vi", "Paladin", cx - 350, cy - 20, "Major", 5, "Vigor", 5, "st_v_2|st_a_1a", "Health and Agility."),
            StarNode("st_bridge_sa", "Spellblade", cx + 350, cy, "Major", 5, "Strength", 5, "st_s_2|st_i_2", "Damage and Mana.")
        ]
        
        for node in raw_nodes:
            self.nodes[node.node_id] = node
        self.nodes["st_root"].is_unlocked = True 

GLOBAL_CONST_DB = ConstellationRegistry()

class ConstellationUI:
    def __init__(self, registry):
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.registry = registry
        self.node_list = list(self.registry.nodes.values())
        
        self.cursor_idx = 0
        for i, n in enumerate(self.node_list):
            if n.node_id == "st_root": self.cursor_idx = i

        self.camera_offset = Vector2(0, 0)
        self.target_camera_offset = Vector2(0, 0)
        self._snap_camera_to_cursor(instant=True)
        
        self.stick_x_pressed = False
        self.stick_y_pressed = False
        self.pulse_timer = 0.0
        
        # AAA Error Feedback System
        self.error_msg = ""
        self.error_timer = 0.0

    def _snap_camera_to_cursor(self, instant=False):
        if len(self.node_list) == 0: return
        target_pos = self.node_list[self.cursor_idx].pos
        self.target_camera_offset = Vector2(WIDTH//2, HEIGHT//2) - target_pos
        if instant: self.camera_offset = Vector2(self.target_camera_offset)

    def update(self, dt):
        self.camera_offset = self.camera_offset.lerp(self.target_camera_offset, min(dt * 10.0, 1.0))
        self.pulse_timer += dt * 5.0
        
        if self.error_timer > 0:
            self.error_timer -= dt
            if self.error_timer <= 0:
                self.error_msg = ""

    def _get_spatial_target(self, current_pos, direction_vec):
        best_idx, best_score = -1, float('inf')
        for i, target in enumerate(self.node_list):
            diff = target.pos - current_pos
            if diff.length() < 5.0: continue 
            dot = diff.normalize().dot(direction_vec)
            if dot > 0.5: 
                score = diff.length() * (1.0 + (1.0 - dot) * 2.0)
                if score < best_score: best_score, best_idx = score, i
        return best_idx

    def _can_refund(self, target_id):
        """Topological graph check: Ensures refunding a node does not orphan other active nodes."""
        if target_id == "st_root": return False
        
        self.registry.nodes[target_id].is_unlocked = False
        is_valid = True
        
        for node in self.node_list:
            if node.is_unlocked and node.node_id != "st_root":
                has_valid_parent = False
                for req_id in node.reqs:
                    if self.registry.nodes[req_id].is_unlocked:
                        has_valid_parent = True
                        break
                
                if not has_valid_parent and len(node.reqs) > 0:
                    is_valid = False
                    break
                    
        self.registry.nodes[target_id].is_unlocked = True
        return is_valid

    def handle_input(self, event, player_inventory):
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]: return "BACK"
        if event.type == pygame.JOYBUTTONDOWN and event.button == 1: return "BACK"

        dx, dy, attempt_unlock, attempt_refund = 0, 0, False, False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: dx = -1
            elif event.key == pygame.K_RIGHT: dx = 1
            elif event.key == pygame.K_UP: dy = -1
            elif event.key == pygame.K_DOWN: dy = 1
            elif event.key == pygame.K_RETURN: attempt_unlock = True
            elif event.key == pygame.K_y: attempt_refund = True
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
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0: attempt_unlock = True
            elif event.button == 3: attempt_refund = True

        if dx != 0 or dy != 0:
            dir_vec = Vector2(dx, dy).normalize() if dx != 0 and dy != 0 else Vector2(dx, dy)
            target_idx = self._get_spatial_target(self.node_list[self.cursor_idx].pos, dir_vec)
            if target_idx != -1:
                self.cursor_idx = target_idx
                self._snap_camera_to_cursor()

        node = self.node_list[self.cursor_idx]
        
        # --- THE LIGHT DOWN / REFUND MECHANIC ---
        if attempt_refund:
            if node.is_unlocked and node.node_id != "st_root":
                if self._can_refund(node.node_id):
                    crystal_item = copy.copy(item_database.GLOBAL_DB.items["mat_magic_crystal"])
                    for _ in range(node.cost):
                        player_inventory.add_item(copy.copy(crystal_item))
                    node.is_unlocked = False
                else:
                    self.error_msg = "Cannot Refund: Node supports other active stars!"
                    self.error_timer = 2.0

        # --- THE LIGHT UP / UNLOCK MECHANIC ---
        elif attempt_unlock:
            if not node.is_unlocked:
                can_unlock = False
                for req_id in node.reqs:
                    if self.registry.nodes[req_id].is_unlocked: can_unlock = True; break
                if not node.reqs: can_unlock = True
                
                total_spent = sum(n.cost for n in self.node_list if n.is_unlocked)
                crystals = player_inventory.count_item("mat_magic_crystal")
                
                if can_unlock:
                    if crystals >= node.cost and (total_spent + node.cost) <= 100:
                        player_inventory.remove_item_by_id("mat_magic_crystal", node.cost)
                        node.is_unlocked = True
                    elif (total_spent + node.cost) > 100:
                        self.error_msg = "Arcane Tube Capacity Reached (Max 100)!"
                        self.error_timer = 2.0
                    else:
                        self.error_msg = "Not enough Magic Crystals!"
                        self.error_timer = 2.0
                        
        return None

    def get_passive_bonuses(self):
        totals = {}
        for node in self.node_list:
            if node.is_unlocked:
                if node.stat_type not in totals: totals[node.stat_type] = 0
                totals[node.stat_type] += node.stat_value
        return totals

    def draw(self, screen, current_crystals):
        screen.fill((5, 5, 12)) 
        
        for node in self.node_list:
            start_pos = node.pos + self.camera_offset
            for req_id in node.reqs:
                if req_id in self.registry.nodes:
                    parent = self.registry.nodes[req_id]
                    end_pos = parent.pos + self.camera_offset
                    color = (255, 215, 0) if (node.is_unlocked and parent.is_unlocked) else (60, 60, 80)
                    width = 4 if (node.is_unlocked and parent.is_unlocked) else 2
                    pygame.draw.line(screen, color, start_pos, end_pos, width)

        for i, node in enumerate(self.node_list):
            draw_pos = node.pos + self.camera_offset
            can_unlock = False
            for req_id in node.reqs:
                if self.registry.nodes[req_id].is_unlocked: can_unlock = True; break
            if not node.reqs: can_unlock = True
                    
            if node.is_unlocked: fill_color = (255, 215, 0); outline_color = (255, 255, 255)
            elif can_unlock: fill_color = (100, 100, 100); outline_color = (0, 255, 100)
            else: fill_color = (20, 20, 20); outline_color = (80, 80, 80)
                
            radius = 12 if node.tier == "Minor" else (20 if node.tier == "Major" else 30)
            pygame.draw.circle(screen, fill_color, draw_pos, radius)
            pygame.draw.circle(screen, outline_color, draw_pos, radius, 3)
            
            if i == self.cursor_idx:
                pulse_offset = abs(math.sin(self.pulse_timer)) * 5.0
                pygame.draw.circle(screen, (255, 255, 255), draw_pos, radius + 8 + pulse_offset, 3)
                
        screen.blit(self.title_font.render("CONSTELLATION OF DESTINY", True, (255,255,255)), (50, 40))
        screen.blit(self.font.render(f"Magic Crystals: {current_crystals} 💎", True, (0, 255, 255)), (50, 80))

        # ==========================================
        # VISUAL GEM RACK (The 100-Capacity Constraint)
        # ==========================================
        total_spent = sum(n.cost for n in self.node_list if n.is_unlocked)
        
        rack_bg = pygame.Rect(20, 110, 110, 430)
        pygame.draw.rect(screen, (15, 15, 20), rack_bg)
        pygame.draw.rect(screen, (50, 50, 60), rack_bg, 2)
        
        screen.blit(self.font.render("ARCANE TUBE", True, (150, 150, 150)), (25, 120))
        cap_color = (255, 50, 50) if total_spent >= 100 else (0, 255, 255)
        screen.blit(self.font.render(f"{total_spent} / 100", True, cap_color), (40, 140))

        drawn_gems = 0
        rack_start_x, rack_start_y = 32, 170
        slot_sz, margin = 12, 5
        
        for row in range(20):
            for col in range(5):
                x = rack_start_x + col * (slot_sz + margin)
                y = rack_start_y + row * (slot_sz + margin)
                rect = pygame.Rect(x, y, slot_sz, slot_sz)
                
                if drawn_gems < total_spent:
                    pygame.draw.rect(screen, (0, 255, 255), rect) 
                    pygame.draw.rect(screen, (255, 255, 255), rect, 1)
                    drawn_gems += 1
                else:
                    pygame.draw.rect(screen, (30, 30, 40), rect)  
                    pygame.draw.rect(screen, (60, 60, 80), rect, 1)

        # INFO PANEL & ERROR RENDERING
        if len(self.node_list) > 0:
            sel_node = self.node_list[self.cursor_idx]
            info_rect = pygame.Rect(WIDTH - 380, HEIGHT - 250, 360, 230)
            pygame.draw.rect(screen, (20, 20, 30), info_rect); pygame.draw.rect(screen, (100, 100, 150), info_rect, 2)
            
            can_unlock = False
            for req_id in sel_node.reqs:
                if self.registry.nodes[req_id].is_unlocked: can_unlock = True; break
            if not sel_node.reqs: can_unlock = True
            
            status = "UNLOCKED" if sel_node.is_unlocked else ("AVAILABLE" if can_unlock else "LOCKED")
            status_color = (255,215,0) if sel_node.is_unlocked else ((0,255,100) if status == "AVAILABLE" else (255,50,50))
            
            if status == "AVAILABLE" and (total_spent + sel_node.cost > 100):
                status = "CAPACITY REACHED"
                status_color = (255, 50, 50)
            
            screen.blit(self.title_font.render(sel_node.name, True, (255,255,255)), (info_rect.x + 20, info_rect.y + 20))
            screen.blit(self.font.render(status, True, status_color), (info_rect.x + 20, info_rect.y + 60))
            
            val_txt = f"+{sel_node.stat_value}" if sel_node.stat_type not in ["Haste", "Reach", "Impact", "Vampire"] else f"+{int(sel_node.stat_value*100)}%"
            screen.blit(self.font.render(f"{val_txt} {sel_node.stat_type}", True, (200,200,200)), (info_rect.x + 20, info_rect.y + 90))
            
            if not sel_node.is_unlocked: screen.blit(self.font.render(f"Cost: {sel_node.cost} Crystals", True, (0,255,255)), (info_rect.x + 20, info_rect.y + 120))
                
            desc_lines = [sel_node.desc[i:i+40] for i in range(0, len(sel_node.desc), 40)]
            for i, line in enumerate(desc_lines): screen.blit(self.font.render(line, True, (150,150,150)), (info_rect.x + 20, info_rect.y + 160 + (i*20)))

            if self.error_timer > 0:
                err_rect = pygame.Rect(WIDTH - 380, HEIGHT - 290, 360, 30)
                pygame.draw.rect(screen, (100, 0, 0), err_rect)
                pygame.draw.rect(screen, (255, 50, 50), err_rect, 2)
                screen.blit(self.font.render(self.error_msg, True, (255, 255, 255)), (err_rect.x + 10, err_rect.y + 8))

        pygame.draw.rect(screen, (10, 10, 15), (0, HEIGHT - 40, WIDTH, 40))
        screen.blit(self.font.render("[Stick/D-Pad] Navigate Sky   |   [A] Unlock Star   |   [Y] Refund Star   |   [B] Back", True, (150, 150, 150)), (WIDTH // 2 - 350, HEIGHT - 28))