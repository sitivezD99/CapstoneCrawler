# entities.py
import pygame
import random
import math
import os
import csv
import copy
from pygame.math import Vector2
from settings import *
from engine.entity import Entity
from engine.physics import move_and_slide
from engine.input import InputManager

# --- src/engine/entities.py ---
try:
    # Use a relative import since they are in the same folder
    from .player_animator import PlayerAnimator 
except (ImportError, ValueError):
    try:
        import engine.player_animator as player_animator
        PlayerAnimator = player_animator.PlayerAnimator
    except ImportError:
        print("[ENTITIES] Warning: player_animator.py not found. Using square fallback.")
        PlayerAnimator = None

class PlayerEquipment:
    def __init__(self, inventory_ref):
        self.inv = inventory_ref
        self.slots = {
            "MainHand": None,
            "OffHand": None,
            "Chest": None,
            "Legs": None,
            "Feet": None,
            "Ring": None,
            "Necklace": None
        }

    def equip(self, item, source_slot=None):
        if not getattr(item, 'equip_slot', None): return False
        slot_name = item.equip_slot
        
        equipped_item = copy.copy(item)
        equipped_item.is_equipped = True

        if source_slot:
            self.inv.remove_slot_item(source_slot, 1)
        else:
            self.inv.remove_item_by_id(item.item_id, 1)

        if self.slots[slot_name]:
            self.unequip(slot_name)
            
        self.slots[slot_name] = equipped_item
        self.inv.add_item(equipped_item) 
        return True

    def unequip(self, slot_name):
        item = self.slots.get(slot_name)
        if item:
            self.inv.unequip_item(item) 
            self.slots[slot_name] = None
            return True
        return False

    def get_total_stats(self):
        stats = {"Base_Damage": 0, "Defense": 0, "Strength": 0, "Vigor": 0}
        for item in self.slots.values():
            if item:
                if item.effect_stat in stats:
                    stats[item.effect_stat] += float(item.effect_value)
        return stats

class PlayerInventory:
    def __init__(self):
        self.slots = []

    def add_item(self, new_item):
        for slot in self.slots:
            if (slot['item'].item_id == new_item.item_id and 
                slot['item'].effect_value == new_item.effect_value and
                getattr(slot['item'], 'is_equipped', False) == getattr(new_item, 'is_equipped', False)):
                
                if slot['count'] < int(new_item.max_stack):
                    slot['count'] += 1
                    return True
        
        self.slots.append({'item': new_item, 'count': 1})
        return True

    def unequip_item(self, item_to_unequip):
        for slot in self.slots:
            if slot['item'].item_id == item_to_unequip.item_id and getattr(slot['item'], 'is_equipped', False):
                slot['count'] -= 1
                if slot['count'] <= 0:
                    self.slots.remove(slot)
                
                item_to_unequip.is_equipped = False
                self.add_item(item_to_unequip)
                return

    def remove_slot_item(self, slot, amount=1):
        slot['count'] -= amount
        if slot['count'] <= 0:
            if slot in self.slots:
                self.slots.remove(slot)

    def count_item(self, item_id):
        total = 0
        for slot in self.slots:
            if slot['item'].item_id == item_id:
                total += slot['count']
        return total
        
    def remove_item_by_id(self, item_id, amount):
        removed = 0
        for slot in reversed(self.slots): 
            if slot['item'].item_id == item_id and not getattr(slot['item'], 'is_equipped', False):
                if slot['count'] <= (amount - removed):
                    removed += slot['count']
                    self.slots.remove(slot)
                else:
                    slot['count'] -= (amount - removed)
                    removed = amount
            if removed >= amount: break

    def get_filtered_slots(self, category_string):
        if category_string == "ALL": return self.slots
        return [s for s in self.slots if s['item'].category.upper() == category_string]

class AttributeManager:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.xp_next = 200
        
        self.base_vigor = 10     
        self.base_strength = 5    
        self.base_agility = 5     
        self.base_intelligence = 5 
        
        self.max_hp = 100
        self.current_hp = 100
        self.max_mana = 50        
        self.current_mana = 50    
        self.damage = 10
        self.defense = 0 
        
        self.update_stats()

    def update_stats(self, constellation_bonuses=None, equipment_bonuses=None):
        cb = constellation_bonuses or {}
        eb = equipment_bonuses or {}
        
        final_vigor = self.base_vigor + cb.get("Vigor", 0) + eb.get("Vigor", 0)
        final_strength = self.base_strength + cb.get("Strength", 0) + eb.get("Strength", 0)
        final_int = self.base_intelligence + cb.get("Intelligence", 0)
        
        self.max_hp = 100 + (final_vigor * 15) + cb.get("Max_HP", 0)
        self.max_mana = 50 + (final_int * 10) + cb.get("Max_Mana", 0)
        self.damage = 10 + (final_strength * 3) + cb.get("Base_Damage", 0) + eb.get("Base_Damage", 0)
        self.defense = eb.get("Defense", 0)
        
        if self.current_hp > self.max_hp: self.current_hp = self.max_hp
        if self.current_mana > self.max_mana: self.current_mana = self.max_mana

    def heal(self, amount):
        self.current_hp = min(self.current_hp + amount, self.max_hp)

    def gain_xp(self, amount, constellation_bonuses=None, equip_bonuses=None):
        if self.level >= 20: return False
        self.xp += amount
        if self.xp >= self.xp_next:
            self.level_up(constellation_bonuses, equip_bonuses)
            return True
        return False

    def level_up(self, constellation_bonuses=None, equip_bonuses=None):
        if self.level < 20:
            self.level += 1
            self.xp = 0
            self.xp_next = int(self.xp_next * 1.4)
            self.base_vigor += 2
            self.base_strength += 1
            self.base_agility += 1
            self.base_intelligence += 1
            self.update_stats(constellation_bonuses, equip_bonuses)
            self.current_hp = self.max_hp

    def force_level(self, direction, constellation_bonuses=None, equip_bonuses=None):
        new_lvl = max(1, min(20, self.level + direction))
        if new_lvl != self.level:
            self.level = new_lvl
            self.base_vigor = 10 + (self.level - 1) * 2
            self.base_strength = 5 + (self.level - 1)
            self.base_agility = 5 + (self.level - 1)
            self.base_intelligence = 5 + (self.level - 1)
            self.update_stats(constellation_bonuses, equip_bonuses)
            self.current_hp = self.max_hp

class TextManager:
    def __init__(self):
        self.texts = []
        self.font = pygame.font.Font(None, 24)

    def add(self, x, y, text, color=(255, 50, 50)):
        self.texts.append({
            'x': x + random.randint(-10, 10), 'y': y + random.randint(-10, 10),
            'text': text, 'color': color, 'life': 1.0, 'vy': -30
        })

    def update(self, dt):
        for t in self.texts:
            t['life'] -= dt
            t['y'] += t['vy'] * dt
        self.texts = [t for t in self.texts if t['life'] > 0]

    def draw(self, screen, camera):
        for t in self.texts:
            alpha = max(0, int(255 * (t['life'] / 0.5))) if t['life'] < 0.5 else 255
            surf = self.font.render(t['text'], True, t['color'])
            surf.set_alpha(alpha)
            screen.blit(surf, camera.apply(surf.get_rect(center=(t['x'], t['y']))))

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 26, 26, (0, 0, 255))
        self.input = InputManager()
        self.attributes = AttributeManager()
        self.inventory = PlayerInventory() 
        self.equipment = PlayerEquipment(self.inventory) 
        self.active_stats = {}
        
        # --- ANIMATION ENGINE ATTACHMENT ---
        if PlayerAnimator:
            self.animator = PlayerAnimator()
        else:
            self.animator = None
        
        self.state = STATE_IDLE
        self.state_timer = 0
        self.aim_direction = Vector2(0, 1) 
        self.move_direction = Vector2(0, 0)
        self.is_invincible = False  
        self.damage_flash_timer = 0.0 
        self.dash_direction = Vector2(0, 0)
        self.dash_cooldown_timer = 0
        self.dash_duration = 0.2
        self.dash_speed_mult = 3.0
        self.dash_cooldown = 1.0
        
        self.enemies_hit = set()
        self.combo_step = 1
        self.current_attack_step = 1 
        self.combo_reset_timer = 0.0
        
        self.skill_1_cooldown_timer = 0
        self.skill_1_cooldown = 3.0
        self.skill_anchor_pos = Vector2(0, 0)
        self.skill_anchor_aim = Vector2(0, 1)
        self.skill_2_cooldown_timer = 0
        self.skill_2_cooldown = 6.0
        self.skill_3_cooldown_timer = 0
        self.skill_3_cooldown = 8.0
        self.spin_angle = 0.0
        self.spin_tick_timer = 0.0 
        
        self.flow_stacks = 0
        self.max_stacks = 10
        self.flow_grace_period = 10.0
        self.flow_grace_timer = self.flow_grace_period
        self.flow_decay_rate = 1.0
        self.flow_decay_timer = self.flow_decay_rate

    def gain_flow(self, amount):
        self.flow_stacks = min(self.flow_stacks + amount, self.max_stacks)
        self.flow_grace_timer = self.flow_grace_period
        self.flow_decay_timer = self.flow_decay_rate

    def take_damage(self, raw_amount, texts, camera):
        if self.is_invincible:
            texts.add(self.rect.centerx, self.rect.top, "DODGED!", (0, 255, 255))
            return
            
        dmg_multiplier = 100.0 / (100.0 + self.attributes.defense)
        actual_damage = raw_amount * dmg_multiplier
        
        self.attributes.current_hp -= actual_damage
        self.flow_stacks = max(0, self.flow_stacks - 3) 
        self.damage_flash_timer = 0.15
        # --- SAFE CHECK: Only shake if the camera supports it ---
        if hasattr(camera, 'add_trauma'):
            camera.add_trauma(0.4) 
            
        texts.add(self.rect.centerx, self.rect.top, f"-{int(actual_damage)}", (255, 0, 0))
        
        if self.attributes.current_hp <= 0:
            print("💀 PLAYER DIED - Resetting HP for Sandbox")
            self.attributes.current_hp = self.attributes.max_hp

    def _get_stats_for_state(self, state):
        if state == STATE_ATTACKING: return self.active_stats.get("BASE COMBO", {})
        elif state == STATE_SKILL_1: return self.active_stats.get("HAMMER (X)", {})
        elif state == STATE_SKILL_2: return self.active_stats.get("STUN (Y)", {})
        elif state == STATE_SKILL_3: return self.active_stats.get("WHIRLWIND (B)", {})
        return {}

    def update(self, dt, walls, skill_stats, combat_allowed=True):
        # 1. Sync stats (Fixes HUD bars)
        self.active_stats = skill_stats 
        
        # 2. Update Animator ONCE with the correct arguments
        if self.animator:
            is_atk = self.state in [STATE_ATTACKING, STATE_SKILL_1, STATE_SKILL_2, STATE_SKILL_3]
            self.animator.update(dt, self.velocity.x, self.velocity.y, is_attacking=is_atk)

        # 3. Handle Physics and Input
        self.handle_input(dt, combat_allowed)
        self.rect = move_and_slide(self.rect, self.velocity, walls)
        
        # 4. Timer Management
        if self.damage_flash_timer > 0: self.damage_flash_timer -= dt
        if self.dash_cooldown_timer > 0: self.dash_cooldown_timer -= dt
        if self.skill_1_cooldown_timer > 0: self.skill_1_cooldown_timer -= dt
        if self.skill_2_cooldown_timer > 0: self.skill_2_cooldown_timer -= dt
        if self.skill_3_cooldown_timer > 0: self.skill_3_cooldown_timer -= dt

        if self.combo_reset_timer > 0 and self.state != STATE_ATTACKING:
            self.combo_reset_timer -= dt
            if self.combo_reset_timer <= 0:
                self.combo_step = 1

        self.is_invincible = (self.state == STATE_DASHING)

        # 5. Whirlwind (Skill 3) Logic
        if self.state == STATE_SKILL_3:
            stats = self._get_stats_for_state(self.state)
            haste_mult = 1.0 - min(stats.get('Haste', 0), 0.5)
            self.spin_angle = (self.spin_angle + 720 * (1.0 / haste_mult) * dt) % 360
            self.spin_tick_timer -= dt
            if self.spin_tick_timer <= 0:
                self.enemies_hit.clear()
                self.spin_tick_timer = 0.25 * haste_mult

        # 6. State Expiration
        if self.state_timer > 0:
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.state in (STATE_ATTACKING, STATE_SKILL_1, STATE_SKILL_2, STATE_SKILL_3):
                    self.state = STATE_COOLDOWN
                    self.state_timer = ATTACK_COOLDOWN
                elif self.state in (STATE_DASHING, STATE_COOLDOWN):
                    self.state = STATE_IDLE

        # 7. State Expiration and Transitions
        if self.state_timer > 0:
            self.state_timer -= dt
            if self.state_timer <= 0:
                if self.state in (STATE_ATTACKING, STATE_SKILL_1, STATE_SKILL_2, STATE_SKILL_3):
                    stats = self._get_stats_for_state(self.state)
                    haste_mult = 1.0 - min(stats.get('Haste', 0), 0.5)
                    self.state = STATE_COOLDOWN
                    self.state_timer = ATTACK_COOLDOWN * haste_mult 
                elif self.state in (STATE_DASHING, STATE_COOLDOWN):
                    self.state = STATE_IDLE

    def handle_input(self, dt, combat_allowed):
        self.move_direction = self.input.get_movement_vector()
        aim_input = self.input.get_aim_vector()
        if aim_input.length() > 0: self.aim_direction = aim_input.normalize()
        elif self.move_direction.length() > 0: self.aim_direction = self.move_direction.normalize()

        speed = PLAYER_MAX_SPEED
        
        if self.state == STATE_DASHING:
            self.velocity = self.dash_direction * (speed * self.dash_speed_mult)
            return 
        elif self.state in (STATE_ATTACKING, STATE_SKILL_2):
            self.velocity = self.velocity.lerp(self.move_direction * (speed * 0.1), 0.2) 
        elif self.state == STATE_SKILL_1:
            self.velocity = self.velocity.lerp(Vector2(0, 0), 0.3) 
        elif self.state == STATE_SKILL_3:
            self.velocity = self.velocity.lerp(self.move_direction * (speed * 0.6), 0.2) 
        else:
            self.velocity = self.velocity.lerp(self.move_direction * speed, 0.2)
            if self.state != STATE_COOLDOWN:
                self.state = STATE_MOVING if self.move_direction.length() > 0 else STATE_IDLE

        if not combat_allowed: return

        can_act = self.state not in (STATE_COOLDOWN, STATE_ATTACKING, STATE_SKILL_1, STATE_SKILL_2, STATE_SKILL_3, STATE_DASHING)

        if self.input.is_dash_pressed() and self.dash_cooldown_timer <= 0 and self.state != STATE_DASHING:
            self.state, self.state_timer, self.dash_cooldown_timer = STATE_DASHING, self.dash_duration, self.dash_cooldown
            self.dash_direction = self.move_direction.normalize() if self.move_direction.length() > 0 else self.aim_direction.normalize()
            self.gain_flow(1)
            
        elif self.input.is_skill_3_pressed() and self.skill_3_cooldown_timer <= 0 and self.attributes.level >= 15 and can_act:
            stats = self.active_stats.get("WHIRLWIND (B)", {})
            haste_mult = 1.0 - min(stats.get('Haste', 0), 0.5)
            self.state = STATE_SKILL_3
            self.state_timer = 2.5 * haste_mult 
            self.skill_3_cooldown_timer = self.skill_3_cooldown * haste_mult 
            self.spin_angle = 0.0
            self.spin_tick_timer = 0.0
            self.enemies_hit.clear()
            
        elif self.input.is_skill_2_pressed() and self.skill_2_cooldown_timer <= 0 and self.attributes.level >= 10 and can_act:
            stats = self.active_stats.get("STUN (Y)", {})
            haste_mult = 1.0 - min(stats.get('Haste', 0), 0.5)
            self.state = STATE_SKILL_2
            self.state_timer = 0.3 * haste_mult 
            self.skill_2_cooldown_timer = self.skill_2_cooldown * haste_mult
            self.enemies_hit.clear()

        elif self.input.is_skill_1_pressed() and self.skill_1_cooldown_timer <= 0 and self.attributes.level >= 5 and can_act:
            stats = self.active_stats.get("HAMMER (X)", {})
            haste_mult = 1.0 - min(stats.get('Haste', 0), 0.5)
            self.state = STATE_SKILL_1
            self.state_timer = 0.5 * haste_mult 
            self.skill_1_cooldown_timer = self.skill_1_cooldown * haste_mult
            self.enemies_hit.clear()
            self.skill_anchor_pos = Vector2(self.rect.center)
            self.skill_anchor_aim = Vector2(self.aim_direction)
            
        elif self.input.is_attack_pressed() and can_act:
            stats = self.active_stats.get("BASE COMBO", {})
            haste_mult = 1.0 - min(stats.get('Haste', 0), 0.5)
            self.state = STATE_ATTACKING
            self.enemies_hit.clear()
            self.current_attack_step = self.combo_step
            
            if self.combo_step in [1, 2]:
                self.state_timer = 0.25 * haste_mult 
                self.velocity += self.aim_direction * (speed * 1.5) 
                self.combo_step += 1
            else: 
                self.state_timer = 0.4 * haste_mult 
                self.velocity += self.aim_direction * (speed * 2.5) 
                self.combo_step = 1 
                
            self.combo_reset_timer = 1.0 

    def _apply_combat_physics(self, enemy, raw_damage, push_dir, knockback_amt, is_heavy, texts, stats, vamp_override=None):
        enemy.interrupt_attack(is_heavy)
        enemy.velocity += push_dir * knockback_amt
        
        vec_to_enemy = (Vector2(enemy.rect.center) - Vector2(self.rect.center))
        dot = vec_to_enemy.normalize().dot(enemy.aim_direction) if vec_to_enemy.length() > 0 else 0
        
        is_crit = False
        color = (255, 255, 255)
        
        if dot > 0.3:
            raw_damage *= 2
            is_crit = True
            color = (255, 215, 0)
            self.gain_flow(2)
        else:
            self.gain_flow(1)

        if dot < -0.3 and enemy.stats.shield_hp > 0:
            enemy.stats.shield_hp -= raw_damage
            if enemy.stats.shield_hp <= 0:
                texts.add(enemy.rect.centerx, enemy.rect.top, "SHIELD BROKEN!", (0, 255, 255))
            else:
                texts.add(enemy.rect.centerx, enemy.rect.top, f"Shield -{int(raw_damage)}", (150, 150, 150))
        else:
            enemy.take_damage(raw_damage)
            texts.add(enemy.rect.centerx, enemy.rect.top, f"{int(raw_damage)}{'!' if is_crit else ''}", color)
            
            actual_vampire = vamp_override if vamp_override is not None else min(stats.get('Vampire', 0), 1.0)
            if actual_vampire > 0:
                heal = raw_damage * actual_vampire
                self.attributes.current_hp = min(self.attributes.current_hp + heal, self.attributes.max_hp)
                texts.add(self.rect.centerx, self.rect.top, f"+{int(heal)}", (50, 255, 50))
                
        if enemy.stats.current_hp <= 0 and enemy.is_alive:
            enemy.is_alive = False
            self.attributes.gain_xp(40)
            return True 
        return False

    def check_attack(self, enemies, texts):
        killed = []
        stats = self._get_stats_for_state(self.state)
        
        if self.state == STATE_ATTACKING:
            self._process_combo_attack(enemies, texts, killed, stats)
        elif self.state == STATE_SKILL_1:
            self._process_hammer_smash(enemies, texts, killed, stats)
        elif self.state == STATE_SKILL_2:
            self._process_stun(enemies, texts, killed, stats)
        elif self.state == STATE_SKILL_3:
            self._process_whirlwind(enemies, texts, killed, stats)
        return killed

    def _process_combo_attack(self, enemies, texts, killed, stats):
        aim_dir = self.aim_direction
        perp_dir = Vector2(-aim_dir.y, aim_dir.x)
        
        force_mult = 1.0 + stats.get('Force', 0)
        reach_mult = 1.0 + min(stats.get('Reach', 0), 1.5) 
        impact_mult = 1.0 + min(stats.get('Impact', 0), 1.0)
        vamp_base = min(stats.get('Vampire', 0), 1.0)
        
        if self.current_attack_step in [1, 2]:
            blade_length = 22 * reach_mult 
            blade_width = 40 * reach_mult  
            damage_mult = 1.0 * force_mult
            knockback = 8 * impact_mult 
            is_heavy = False
            vamp_override = vamp_base
        else: 
            blade_length = 37 * reach_mult 
            blade_width = 15 * reach_mult  
            damage_mult = 1.5 * force_mult
            knockback = 18 * impact_mult 
            is_heavy = True
            vamp_override = (vamp_base + 0.05) if vamp_base > 0 else 0 
            
        for e in enemies:
            if e not in self.enemies_hit and e.is_alive:
                vec_to_enemy = Vector2(e.rect.center) - Vector2(self.rect.center)
                proj_fwd = vec_to_enemy.dot(aim_dir)
                proj_side = vec_to_enemy.dot(perp_dir)
                
                if (-10 <= proj_fwd <= blade_length + 13) and (abs(proj_side) <= (blade_width / 2) + 13):
                    self.enemies_hit.add(e)
                    raw_dmg = self.attributes.damage * damage_mult
                    if self._apply_combat_physics(e, raw_dmg, self.aim_direction, knockback, is_heavy, texts, stats, vamp_override):
                        killed.append(e)

    def _process_hammer_smash(self, enemies, texts, killed, stats):
        force_mult = 1.0 + stats.get('Force', 0)
        reach_mult = 1.0 + min(stats.get('Reach', 0), 1.5)
        impact_mult = 1.0 + min(stats.get('Impact', 0), 1.0)
        vamp_override = stats.get('Vampire', 0) 
        
        cone_range = 90 * reach_mult 
        
        for e in enemies:
            if e not in self.enemies_hit and e.is_alive:
                vec_to_enemy = Vector2(e.rect.center) - self.skill_anchor_pos
                dist = vec_to_enemy.length()
                if 0 < dist <= cone_range:
                    vec_to_enemy_norm = vec_to_enemy.normalize()
                    angle = self.skill_anchor_aim.angle_to(vec_to_enemy_norm)
                    if abs(angle) <= 30: 
                        self.enemies_hit.add(e)
                        raw_dmg = (self.attributes.damage * 2.5) * force_mult
                        knockback = 25 * impact_mult 
                        if self._apply_combat_physics(e, raw_dmg, self.skill_anchor_aim, knockback, True, texts, stats, vamp_override):
                            killed.append(e)

    def _process_stun(self, enemies, texts, killed, stats):
        stun_radius = 37 * (1.0 + min(stats.get('Reach', 0), 1.5)) 
        force_mult = 1.0 + stats.get('Force', 0)
        
        vamp_base = stats.get('Vampire', 0)
        vamp_override = max(0.01, vamp_base - 0.04) if vamp_base > 0 else 0 
        
        for e in enemies:
            if e not in self.enemies_hit and e.is_alive:
                vec_to_enemy = Vector2(e.rect.center) - Vector2(self.rect.center)
                dist = vec_to_enemy.length()
                if 0 < dist <= stun_radius:
                    self.enemies_hit.add(e)
                    push_dir = vec_to_enemy.normalize() if dist > 0 else Vector2(0,1)
                    raw_dmg = (self.attributes.damage * 0.5) * force_mult
                    
                    is_dead = self._apply_combat_physics(e, raw_dmg, push_dir, 2, False, texts, stats, vamp_override)
                    e.apply_stun(3.0) 
                    texts.add(e.rect.centerx, e.rect.top - 20, "STUNNED!", (255, 255, 0))
                    if is_dead: killed.append(e)

    def _process_whirlwind(self, enemies, texts, killed, stats):
        reach_mult = 1.0 + min(stats.get('Reach', 0), 1.5)
        force_mult = 1.0 + stats.get('Force', 0)
        
        vamp_base = stats.get('Vampire', 0)
        vamp_override = (vamp_base + 0.05) if vamp_base > 0 else 0 
        
        blade_length = 45 * reach_mult 
        blade_width = 12 * reach_mult  
        spin_dir = Vector2(1, 0).rotate(self.spin_angle)
        spin_perp = Vector2(0, 1).rotate(self.spin_angle)
        
        for e in enemies:
            if e not in self.enemies_hit and e.is_alive:
                vec_to_enemy = Vector2(e.rect.center) - Vector2(self.rect.center)
                dist = vec_to_enemy.length()
                push_dir = vec_to_enemy.normalize() if dist > 0 else Vector2(0,1)
                
                proj_fwd = vec_to_enemy.dot(spin_dir)
                proj_side = vec_to_enemy.dot(spin_perp)
                
                if (0 <= proj_fwd <= blade_length + 13) and (abs(proj_side) <= (blade_width / 2) + 13):
                    self.enemies_hit.add(e)
                    raw_dmg = self.attributes.damage * force_mult
                    if self._apply_combat_physics(e, raw_dmg, push_dir, 11, False, texts, stats, vamp_override):
                        killed.append(e)
                else:
                    if 0 < dist <= blade_length + 13:
                        enemy_angle = math.degrees(math.atan2(vec_to_enemy.y, vec_to_enemy.x))
                        rel_angle = (enemy_angle - self.spin_angle + 180) % 360 - 180
                        if -90 <= rel_angle < -10: 
                            self.enemies_hit.add(e)
                            raw_dmg = (self.attributes.damage * 0.3) * force_mult
                            if self._apply_combat_physics(e, raw_dmg, push_dir, 0, False, texts, stats, vamp_override):
                                killed.append(e)

    def draw(self, screen, camera):
        colors = {
            STATE_DASHING: (0,255,255),  
            STATE_ATTACKING: (255,215,0), 
            STATE_SKILL_1: (255, 100, 0), 
            STATE_SKILL_2: (150, 0, 255), 
            STATE_SKILL_3: (0, 255, 100), 
            STATE_COOLDOWN: (100,100,100), 
            STATE_MOVING: (50,150,255), 
            STATE_IDLE: (50,50,255)
        }
        
        start = camera.apply(self.rect).center

        # --- NEW ANIMATION DRAW LOGIC ---
        if self.animator:
            try:
                # 1. Ask the animator for the current frame
                frame = self.animator.get_current_image()
                
                # 2. Center it on the player's collision rect
                frame_rect = frame.get_rect(center=start)
                
                # 3. Handle Damage Flashing (tinting the sprite red)
                if self.damage_flash_timer > 0:
                    flash = frame.copy()
                    flash.fill((255, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
                    screen.blit(flash, frame_rect)
                else:
                    # 4. Normal Draw
                    screen.blit(frame, frame_rect)
            except Exception as e:
                # If something goes wrong with the image, default back to drawing boxes
                if self.damage_flash_timer > 0: self.color = (255, 0, 0)
                else: self.color = colors.get(self.state, (255,255,255))
                super().draw(screen, camera)
        else:
            # If assets.py wasn't found at all, draw the default boxes
            if self.damage_flash_timer > 0: self.color = (255, 0, 0)
            else: self.color = colors.get(self.state, (255,255,255))
            super().draw(screen, camera)
        # ---------------------------------
            
        if self.is_invincible:
            pygame.draw.circle(screen, (0, 255, 255), start, 20, 2)
            
        stats = self._get_stats_for_state(self.state)
        reach_mult = 1.0 + min(stats.get('Reach', 0), 1.5)
        
        if self.state == STATE_ATTACKING:
            if self.current_attack_step in [1, 2]: blade_len, blade_w = 22 * reach_mult, 40 * reach_mult 
            else: blade_len, blade_w = 37 * reach_mult, 15 * reach_mult 
            
            dir_vec = self.aim_direction
            perp_vec = Vector2(-dir_vec.y, dir_vec.x)
            
            bl = start - dir_vec * 10 + perp_vec * (blade_w / 2)
            br = start - dir_vec * 10 - perp_vec * (blade_w / 2)
            tl = bl + dir_vec * (blade_len + 10)
            tr = br + dir_vec * (blade_len + 10)
            
            atk_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(atk_surf, COLOR_HITBOX, [bl, tl, tr, br])
            screen.blit(atk_surf, (0,0))
            
        elif self.state == STATE_SKILL_1:
            cone_range = 90 * reach_mult 
            anchor_rect = pygame.Rect(self.skill_anchor_pos.x, self.skill_anchor_pos.y, 0, 0)
            anchor_start = camera.apply(anchor_rect).center
            left_bound = self.skill_anchor_aim.rotate(-30) * cone_range  
            right_bound = self.skill_anchor_aim.rotate(30) * cone_range
            
            pygame.draw.line(screen, (255, 100, 0), anchor_start, anchor_start + left_bound, 3)
            pygame.draw.line(screen, (255, 100, 0), anchor_start, anchor_start + right_bound, 3)
            cone_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA) 
            pygame.draw.polygon(cone_surf, (255, 100, 0, 80), [anchor_start, anchor_start + left_bound, anchor_start + right_bound])
            screen.blit(cone_surf, (0,0))
            
        elif self.state == STATE_SKILL_2:
            radius = int(37 * reach_mult) 
            pygame.draw.circle(screen, (150, 0, 255), start, radius, 3)  
            circle_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (150, 0, 255, 80), start, radius)
            screen.blit(circle_surf, (0,0))
            
        elif self.state == STATE_SKILL_3:
            blade_len = 45 * reach_mult 
            blade_w = 12 * reach_mult 
            dir_vec = Vector2(1, 0).rotate(self.spin_angle)
            perp_vec = Vector2(0, 1).rotate(self.spin_angle)
            bl = start + perp_vec * (blade_w / 2)
            br = start - perp_vec * (blade_w / 2)
            tl = bl + dir_vec * blade_len
            tr = br + dir_vec * blade_len
            
            spin_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(spin_surf, (0, 255, 100, 150), [bl, tl, tr, br])
            trail_points = [start]
            for step in range(0, -95, -15): 
                trail_points.append(start + Vector2(blade_len, 0).rotate(self.spin_angle + step))
            pygame.draw.polygon(spin_surf, (0, 255, 100, 40), trail_points)
            screen.blit(spin_surf, (0,0))

        if self.state != STATE_SKILL_3:
            pygame.draw.line(screen, (255,255,255), start, start + (self.aim_direction * 30), 2)

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 26, 26, (200, 50, 50))
        self.stats = type('obj', (object,), {'max_hp': 60, 'current_hp': 60, 'speed': 0.65, 'shield_hp': 30, 'damage': 15})()
        self.aim_direction = Vector2(0, 1)
        self.state = ENEMY_CHASING
        self.state_timer = 0.0
        self.attack_range = 45 
        self.attack_visual_timer = 0.0 

    def apply_stun(self, duration):
        self.state = ENEMY_STUNNED
        self.state_timer = duration
        
    def interrupt_attack(self, is_heavy=False):
        if self.state in [ENEMY_WINDUP, ENEMY_CHASING, ENEMY_RECOVERING]:
            self.state = ENEMY_STAGGERED
            self.state_timer = 0.45 if is_heavy else 0.25 
            self.attack_visual_timer = 0.0 

    def take_damage(self, amount):
        self.stats.current_hp -= amount

    def update(self, dt, player, walls, texts, camera):
        self.velocity = self.velocity.lerp(Vector2(0, 0), 0.15)
        self.rect = move_and_slide(self.rect, self.velocity, walls)
        
        if self.attack_visual_timer > 0: self.attack_visual_timer -= dt

        vec_to_player = Vector2(player.rect.center) - Vector2(self.rect.center)
        dist_to_player = vec_to_player.length()
        
        if self.state == ENEMY_STUNNED:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = ENEMY_CHASING
                
        elif self.state == ENEMY_STAGGERED:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = ENEMY_CHASING
                
        elif self.state == ENEMY_RECOVERING:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = ENEMY_CHASING
                
        elif self.state == ENEMY_WINDUP:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.attack_visual_timer = 0.15 
                if dist_to_player <= self.attack_range + 20: 
                    player.take_damage(self.stats.damage, texts, camera)
                self.state = ENEMY_RECOVERING
                self.state_timer = 0.4 
                
        elif self.state == ENEMY_CHASING:
            if dist_to_player <= self.attack_range:
                self.state = ENEMY_WINDUP
                self.state_timer = 0.40 
            else:
                if dist_to_player > 0:
                    self.aim_direction = self.aim_direction.lerp(vec_to_player.normalize(), 0.05).normalize()
                target_vel = self.aim_direction * (self.stats.speed * PLAYER_MAX_SPEED)
                self.velocity = self.velocity.lerp(target_vel, 0.1)

    def draw(self, screen, camera):
        if self.state == ENEMY_STUNNED: self.color = (150, 150, 0) 
        elif self.state == ENEMY_STAGGERED: self.color = (100, 150, 200) 
        elif self.state == ENEMY_WINDUP: self.color = (255, 255, 255) 
        elif self.state == ENEMY_RECOVERING: self.color = (100, 50, 50) 
        else: self.color = (200, 50, 50) 
        
        super().draw(screen, camera)
        start = camera.apply(self.rect).center

        if self.attack_visual_timer > 0:
            end_strike = start + (self.aim_direction * (self.attack_range + 20))
            pygame.draw.line(screen, (255, 0, 0), start, end_strike, 8)

        if self.stats.shield_hp > 0:
            pygame.draw.line(screen, (150, 150, 150), start, start + (self.aim_direction * 20), 5)
        else:
            pygame.draw.line(screen, (255, 0, 0), start, start + (self.aim_direction * 20), 2)

class ItemDrop:
    def __init__(self, x, y, item):
        self.item = item
        self.x = x
        self.y = y
        self.z = 10.0 
        
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(40, 90)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.vz = random.uniform(150, 250) 
        
        self.gravity = 800.0
        self.bounce_dampening = 0.5
        self.is_settled = False
        self.pickup_delay = 0.5 
        
        self.rect = pygame.Rect(x-10, y-10, 20, 20)
        try: self.icon_font = pygame.font.SysFont(['segoe ui emoji', 'apple color emoji', 'noto color emoji'], 24)
        except: self.icon_font = pygame.font.Font(None, 24)

    def update(self, dt, player):
        if self.pickup_delay > 0:
            self.pickup_delay -= dt

        if not self.is_settled:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.z += self.vz * dt
            self.vz -= self.gravity * dt 

            if self.z <= 0:
                self.z = 0
                if abs(self.vz) < 50: 
                    self.is_settled = True
                    self.vx = 0
                    self.vy = 0
                    self.vz = 0
                else:
                    self.vz = -self.vz * self.bounce_dampening
                    self.vx *= 0.6
                    self.vy *= 0.6

        self.rect.center = (self.x, self.y)

        if self.is_settled and self.pickup_delay <= 0:
            vec_to_player = Vector2(player.rect.center) - Vector2(self.x, self.y)
            dist = vec_to_player.length()
            
            if dist < 30: 
                return True 
            elif dist < 90: 
                dir = vec_to_player.normalize()
                self.x += dir.x * 250 * dt
                self.y += dir.y * 250 * dt
                
        return False

    def draw(self, screen, camera):
        shadow_rect = camera.apply(pygame.Rect(self.x - 8, self.y - 4, 16, 8))
        shadow_surf = pygame.Surface((16, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, 16, 8))
        screen.blit(shadow_surf, shadow_rect.topleft)

        draw_y = self.y - self.z
        item_rect = camera.apply(pygame.Rect(self.x - 10, draw_y - 10, 20, 20))

        pygame.draw.rect(screen, self.item.color, item_rect, 2)
        try:
            icon_surf = self.icon_font.render(self.item.icon, True, (255, 255, 255))
            screen.blit(icon_surf, icon_surf.get_rect(center=item_rect.center))
        except: pass

class GlyphOre(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.is_ore = True
        self.stats.max_hp = 5
        self.stats.current_hp = 5
        self.stats.shield_hp = 0
        
        # Make the hitbox slightly wider than a standard enemy
        self.rect.inflate_ip(10, 10) 

    def interrupt_attack(self, is_heavy=False):
        # It's a rock! It doesn't flinch or get staggered.
        # But we use the visual timer to trigger a white flash when hit.
        self.attack_visual_timer = 0.1 

    def update(self, dt, player, walls, texts, camera):
        # Absolutely stationary. No AI. No movement.
        self.velocity = Vector2(0, 0)
        if self.attack_visual_timer > 0: self.attack_visual_timer -= dt

    def draw(self, screen, camera):
        # Draw a beautiful crystal polygon instead of an enemy sprite
        start = camera.apply(self.rect).center
        cx, cy = start
        
        # A 3D-looking Diamond shape
        pts = [(cx, cy - 20), (cx + 15, cy), (cx, cy + 20), (cx - 15, cy)]
        
        # Base Color: Arcane Purple. Flash White if struck.
        color = (255, 255, 255) if self.attack_visual_timer > 0 else (138, 43, 226)
        
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, (200, 200, 255), pts, 2) # Glowing outline
        
        # Tiny inner core
        pygame.draw.circle(screen, (255, 215, 0), (cx, cy), 3)