# src/main.py
import pygame
import sys
import random
import copy
import math
import traceback
from pygame.math import Vector2 
from settings import *

# --- World & Engine Imports ---
from world.universe import UniverseManager 
from engine.camera import Camera

# --- UI Imports ---
from ui.hud import HUD
from ui.debug import DebugInterface
from ui.text_manager import TextManager
from ui.inventory_ui import InventoryUI 
from ui.stats_equip_ui import StatsEquipUI
from ui.dev_vault_ui import DevVaultUI 

# --- Entity & System Imports ---
from engine.entities import Player, Enemy, ItemDrop, GlyphOre 
from engine.hex_system import HexCoreUI
from engine.constellation_system import ConstellationUI, GLOBAL_CONST_DB

# Import item_database from its new home in the assets folder
try:
    import src.engine.item_database as item_database
except ImportError:
    try:
        import engine.item_database as item_database
    except ImportError:
        import item_database

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Capstone Crawler | Shattered Atlas")
        self.clock = pygame.time.Clock()

        # 1. Initialize Procedural World
        self.world = UniverseManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        print("[SYSTEM] Searching for safe land...")
        spawn_x, spawn_y = self.world.surface_generator.find_spawn_point()
        
        # 2. Initialize Advanced RPG Player
        self.player = Player(spawn_x, spawn_y)
        print(f"[SYSTEM] Player spawned at {spawn_x}, {spawn_y}")
        
        # --- CAMERA SNAP FIX ---
        # Fast-forward the camera physics so it instantly warps to the player
        for _ in range(50):
            try:
                self.camera.update(self.player, 0.1)
            except TypeError:
                self.camera.update(self.player)
        # -----------------------
        
        self.texts = TextManager()
        self.debug = DebugInterface(self.player, self.world, self.clock)
        
        # 3. Initialize RPG UI Systems
        self.hex_ui = HexCoreUI()
        self.inv_ui = InventoryUI(self.player.inventory) 
        self.stats_ui = StatsEquipUI(self.player.attributes, self.player.equipment, self.player.inventory) 
        self.star_tree = ConstellationUI(GLOBAL_CONST_DB) 
        self.dev_vault = DevVaultUI(item_database.GLOBAL_DB)
        self.hud = HUD()
        
        # 4. Entity Management
        self.enemies = []
        self.loot_drops = [] 
        self.spawn_timer = 2.0
        
        # 5. Menu State Machine
        self.active_menu = None
        self.hub_selection = None
        self.hub_focus_offset = Vector2(0, 0)
        
        self.transition_state = "NONE" 
        self.transition_progress = 0.0
        self.next_menu = None
        
        self.combat_lockout = 0.0
        self.menu_transitions = {
            "STARS": Vector2(0, 1),       
            "GRID": Vector2(0, -1),       
            "INVENTORY": Vector2(1, 0),   
            "STATS_EQUIP": Vector2(-1, 0),
            "VAULT": Vector2(0, -1)
        }
        
        self.menu_btn_was_pressed = False 
        self.stick_x_pressed = False
        self.stick_y_pressed = False

    def ease_out_quart(self, t):
        return 1.0 - math.pow(1.0 - t, 4)

    def trigger_transition(self, target):
        if self.transition_state != "NONE": return
        
        if target in self.menu_transitions and self.active_menu == "HUB":
            self.transition_state = "IN"
            self.transition_progress = 0.0
            self.next_menu = target
            
            if target == "INVENTORY": self.inv_ui.reset()
            elif target == "VAULT": self.dev_vault.reset()
            elif target == "STATS_EQUIP": self.stats_ui.reset()
            
        elif target == "HUB" and self.active_menu in self.menu_transitions:
            self.transition_state = "OUT"
            self.transition_progress = 0.0
            self.next_menu = "HUB"
            self.hub_selection = self.active_menu 
            
        elif target is None:
            self.active_menu = None
            self.hub_selection = None
            self.combat_lockout = 0.3
            
        elif target == "HUB" and self.active_menu is None:
            self.active_menu = "HUB"
            self.hub_selection = None

    def draw_hub_menu(self, push_offset=Vector2(0,0)):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 15, 200)) 
        self.screen.blit(overlay, (0,0))
        font_med = pygame.font.Font(None, 48) 
        
        cx = (WIDTH // 2) + self.hub_focus_offset.x + push_offset.x
        cy = (HEIGHT // 2) + self.hub_focus_offset.y + push_offset.y
        
        def render_option(text, state_id, offset_pos, base_color):
            abs_pos = (cx + offset_pos[0], cy + offset_pos[1])
            if self.hub_selection == state_id:
                surf = font_med.render(text, True, (255, 255, 255))
                bg_rect = surf.get_rect(center=abs_pos).inflate(40, 20)
                pygame.draw.rect(self.screen, (40, 40, 50), bg_rect, border_radius=10)
                pygame.draw.rect(self.screen, base_color, bg_rect, 2, border_radius=10)
            else:
                dim_color = (max(50, base_color[0]-100), max(50, base_color[1]-100), max(50, base_color[2]-100))
                surf = font_med.render(text, True, dim_color)
            self.screen.blit(surf, surf.get_rect(center=abs_pos))

        render_option("↑ Constellation", "STARS", (0, -150), (0, 255, 255))
        render_option("↓ Hex-Core Glyphs", "GRID", (0, 150), (255, 100, 50))
        render_option("← Item Bag", "INVENTORY", (-250, 0), (150, 150, 255))
        render_option("Stats & Equipment →", "STATS_EQUIP", (250, 0), (255, 215, 0))

        font_small = pygame.font.Font(None, 24)
        pygame.draw.rect(self.screen, (10, 10, 15), (0, HEIGHT - 40, WIDTH, 40))
        legend_text = "[Stick/D-Pad] Double-Tap to Enter   | [START] Back/Resume"
        legend_surf = font_small.render(legend_text, True, (150, 150, 150))
        self.screen.blit(legend_surf, (WIDTH // 2 - legend_surf.get_width() // 2, HEIGHT - 28))

    def _draw_specific_menu(self, menu_name, surface):
        if menu_name == "GRID": self.hex_ui.draw(surface, self.player.attributes.level, self.player.inventory)
        elif menu_name == "INVENTORY": self.inv_ui.draw(surface)
        elif menu_name == "STATS_EQUIP": self.stats_ui.draw(surface)
        elif menu_name == "STARS": self.star_tree.draw(surface, self.player.inventory.count_item("mat_magic_crystal"))
        elif menu_name == "VAULT": self.dev_vault.draw(surface)

    def run(self):
        print("\n[SYSTEM] Capstone Engine Fully Initialized.")
        while True:
            try:
                dt = self.clock.tick(FPS) / 1000.0 
                
                # --- UI Transition Logic ---
                target_focus = Vector2(0, 0)
                if self.hub_selection == "STARS": target_focus = Vector2(0, 150)
                elif self.hub_selection == "GRID": target_focus = Vector2(0, -150)
                elif self.hub_selection == "INVENTORY": target_focus = Vector2(250, 0)
                elif self.hub_selection == "STATS_EQUIP": target_focus = Vector2(-250, 0)
            
                t_lerp = min(dt * 15.0, 1.0)
                self.hub_focus_offset = self.hub_focus_offset.lerp(target_focus, t_lerp)

                if self.transition_state != "NONE":
                    self.transition_progress += dt * 3.5 
                    if self.transition_progress >= 1.0:
                        self.transition_progress = 1.0
                        if self.transition_state == "IN": self.active_menu = self.next_menu
                        elif self.transition_state == "OUT": self.active_menu = "HUB"
                        self.transition_state = "NONE"
                        self.next_menu = None

                self.star_tree.update(dt)
                self.inv_ui.update(dt)
                self.stats_ui.update(dt)
                self.hex_ui.update(dt)
                self.dev_vault.update(dt) 

                menu_down = self.player.input.is_menu_pressed()
                if menu_down and not self.menu_btn_was_pressed:
                    if self.transition_state == "NONE":
                        if self.active_menu is None: self.trigger_transition("HUB")
                        elif self.active_menu == "HUB": self.trigger_transition(None) 
                        else: self.trigger_transition("HUB") 

                self.menu_btn_was_pressed = menu_down
                self.player.attributes.update_stats(self.star_tree.get_passive_bonuses(), self.player.equipment.get_total_stats())
                
                # --- Input Events ---
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: 
                        pygame.quit()
                        sys.exit()
                        
                    if event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED): 
                        if hasattr(self.player, 'input'):
                            self.player.input.handle_hotplug(event)
                            
                    if event.type == pygame.KEYDOWN:
                        # Debug & World Layer Controls (From main.py)
                        if event.key == pygame.K_F3: self.debug.toggle()
                        # --- THE NEW G-CHEAT LOGIC ---
                        if event.key == pygame.K_g: 
                            self.world.toggle_layer(self.player)
                            
                            # THE FIX: Wipe all monsters, ores, and loot from the previous layer!
                            self.enemies.clear()
                            self.loot_drops.clear()
                            
                            # Snap camera instantly so you don't watch it fly across the void
                            for _ in range(50):
                                try: self.camera.update(self.player, 0.1)
                                except TypeError: self.camera.update(self.player)
                        # -----------------------------
                        # Level Cheats (From sandbox_main.py)
                        if event.key in [pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS]: 
                            self.player.attributes.force_level(1, self.star_tree.get_passive_bonuses(), self.player.equipment.get_total_stats())
                        if event.key in [pygame.K_MINUS, pygame.K_KP_MINUS]: 
                            self.player.attributes.force_level(-1, self.star_tree.get_passive_bonuses(), self.player.equipment.get_total_stats())

                    if self.transition_state != "NONE": continue 

                    # Active UI Event Handling
                    if self.player.input.is_inventory_pressed(event):
                        if self.active_menu == "INVENTORY": self.trigger_transition("HUB")
                        else: 
                            self.hub_selection = "INVENTORY" 
                            self.trigger_transition("INVENTORY")
                        continue

                    if self.active_menu == "HUB":
                        dx, dy, confirm, back = 0, 0, False, False
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_UP: dy = -1
                            elif event.key == pygame.K_DOWN: dy = 1
                            elif event.key == pygame.K_LEFT: dx = -1
                            elif event.key == pygame.K_RIGHT: dx = 1
                            elif event.key == pygame.K_RETURN: confirm = True
                            elif event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]: back = True
                            elif event.key == pygame.K_y: self.trigger_transition("VAULT"); continue 
                        elif event.type == pygame.JOYHATMOTION:
                            hx, hy = event.value
                            dx, dy = hx, -hy
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
                            if event.button == 0: confirm = True
                            elif event.button == 1: back = True
                            elif event.button == 3: self.trigger_transition("VAULT"); continue

                        target = None
                        if dy == -1: target = "STARS"
                        elif dy == 1: target = "GRID"
                        elif dx == -1: target = "INVENTORY"
                        elif dx == 1: target = "STATS_EQUIP"
                        
                        if target:
                            if self.hub_selection == target: self.trigger_transition(target)
                            else: self.hub_selection = target
                        elif confirm and self.hub_selection: self.trigger_transition(self.hub_selection)
                        elif back:
                            if self.hub_selection is not None: self.hub_selection = None 
                            else: self.trigger_transition(None) 
                        continue 
                    
                    elif self.active_menu == "GRID":
                        if self.hex_ui.handle_input(event, self.player.inventory, self.player.attributes.level) == "BACK": 
                            self.trigger_transition("HUB")
                        
                    elif self.active_menu == "VAULT":
                        req = self.dev_vault.handle_input(event, self.player.inventory)
                        if req == "BACK": self.trigger_transition("HUB")
                        elif req == "SPAWNED": self.texts.add(self.player.rect.centerx, self.player.rect.top, "Items Spawned!", (255,215,0))

                    elif self.active_menu == "STATS_EQUIP":
                        req = self.stats_ui.handle_input(event)
                        if req == "BACK": self.trigger_transition("HUB")
                        elif isinstance(req, dict):
                            if req['action'] == "UNEQUIP":
                                self.player.equipment.unequip(req['slot_name'])
                                self.texts.add(self.player.rect.centerx, self.player.rect.top, "UNEQUIPPED!", (150, 150, 150))
                            elif req['action'] == "EQUIP":
                                self.player.equipment.equip(req['item'])
                                self.texts.add(self.player.rect.centerx, self.player.rect.top, "EQUIPPED!", (255, 215, 0))
                                if hasattr(self.camera, 'add_trauma'): self.camera.add_trauma(0.5) 
                        
                    elif self.active_menu == "INVENTORY":
                        action_req = self.inv_ui.handle_input(event)
                        if action_req == "BACK": self.trigger_transition("HUB")
                        elif isinstance(action_req, dict):
                            act = action_req.get('action')
                            slot = action_req.get('slot')
                            item = action_req.get('item')
                            if not item and slot: item = slot.get('item')
                            
                            if act == "USE" and item and slot:
                                if self.player.attributes.current_hp >= self.player.attributes.max_hp:
                                    self.texts.add(self.player.rect.centerx, self.player.rect.top, "HP FULL!", (200, 200, 200))
                                else:
                                    self.player.attributes.heal(float(item.effect_value))
                                    self.player.inventory.remove_slot_item(slot, 1)
                                    self.texts.add(self.player.rect.centerx, self.player.rect.top, f"+{item.effect_value} HP", (50, 255, 50))
                                    if hasattr(self.camera, 'add_trauma'): self.camera.add_trauma(0.3)
                            elif act == "DROP_ALL" and slot:
                                self.player.inventory.remove_slot_item(slot, slot['count'])
                            elif act == "DROP 1" and slot:
                                self.player.inventory.remove_slot_item(slot, 1)
                            elif act == "EQUIP" and item:
                                success = self.player.equipment.equip(item, source_slot=slot)
                                if success:
                                    self.texts.add(self.player.rect.centerx, self.player.rect.top, "EQUIPPED!", (255, 215, 0))
                                    if hasattr(self.camera, 'add_trauma'): self.camera.add_trauma(0.5)
                            elif act == "UNEQUIP" and item:
                                self.player.equipment.unequip(item.equip_slot)
                                self.texts.add(self.player.rect.centerx, self.player.rect.top, "UNEQUIPPED!", (150, 150, 150))
                            
                    elif self.active_menu == "STARS":
                        if self.star_tree.handle_input(event, self.player.inventory) == "BACK": self.trigger_transition("HUB")

                # --- Game Core Logic (Only active when out of menus) ---
                if self.active_menu is None and self.transition_state == "NONE":
                    if self.combat_lockout > 0:
                        self.combat_lockout -= dt
                        
                    # Collision Gathering
                    nearby_walls = self.world.get_nearby_walls(self.player.rect)
                    
                    # Portals Check
                    if self.world.check_portals(self.player):
                        nearby_walls = self.world.get_nearby_walls(self.player.rect)
                        
                    # --- Infinite World Adaptive Spawning ---
                    self.spawn_timer -= dt
                    if self.spawn_timer <= 0 and len(self.enemies) < 15: 
                        self.spawn_timer = 2.0 
                        # Try up to 10 times to find a safe off-screen spot
                        for _ in range(10):
                            test_x = self.player.rect.centerx + random.choice([-1, 1]) * random.randint(500, 900)
                            test_y = self.player.rect.centery + random.choice([-1, 1]) * random.randint(500, 900)
                            test_rect = pygame.Rect(test_x - 13, test_y - 13, 26, 26)
                            if not self.world.get_nearby_walls(test_rect):
                                self.enemies.append(Enemy(test_x, test_y))
                                break # Found a spot, stop trying! 

                    # Physics and Combat Update
                    self.player.update(dt, nearby_walls, self.hex_ui.skill_stats, combat_allowed=(self.combat_lockout <= 0))
                    killed_enemies = self.player.check_attack(self.enemies, self.texts)
                    
                    if killed_enemies:
                        loot_pool = item_database.GLOBAL_DB.get_enemy_loot_pool()
                        glyph_pool = item_database.GLOBAL_DB.get_all_glyphs()
                        
                        for enemy in killed_enemies:
                            if getattr(enemy, 'is_ore', False):
                                # --- THE MIRACLE DROP MATH ---
                                roll = random.random()
                                target_rarity = "Rare"      # 70% Base Chance
                                if roll > 0.99: target_rarity = "Legendary" # 1% Miracle!
                                elif roll > 0.94: target_rarity = "Mythic"  # 5%
                                elif roll > 0.70: target_rarity = "Epic"    # 24%
                                
                                possible_glyphs = [g for g in glyph_pool if g.rarity == target_rarity]
                                if possible_glyphs:
                                    item = copy.copy(random.choice(possible_glyphs))
                                    self.loot_drops.append(ItemDrop(enemy.rect.centerx, enemy.rect.centery, item))
                                    
                                # Ores also have a 50% chance to drop bonus crystals
                                if random.random() < 0.5:
                                    cryst = copy.copy(item_database.GLOBAL_DB.items["mat_magic_crystal"])
                                    self.loot_drops.append(ItemDrop(enemy.rect.centerx, enemy.rect.centery, cryst))

                            else:
                                # --- NORMAL MONSTER LOOT ---
                                if random.random() < 0.4: 
                                    item = copy.copy(random.choice(loot_pool))
                                    self.loot_drops.append(ItemDrop(enemy.rect.centerx, enemy.rect.centery, item))
                                if random.random() < 0.2: 
                                    cryst = copy.copy(item_database.GLOBAL_DB.items["mat_magic_crystal"])
                                    self.loot_drops.append(ItemDrop(enemy.rect.centerx, enemy.rect.centery, cryst))
                            
                    # --- SMART SPAWNING / RECYCLING LOGIC ---
                    DESPAWN_DISTANCE = 1400  
                    SPAWN_MIN = 500          
                    SPAWN_MAX = 900          
                    
                    # 1. ORE GENERATION (Cave Layer Only)
                    if getattr(self.world, 'current_layer', 0) == -1:
                        active_ores = [e for e in self.enemies if getattr(e, 'is_ore', False)]
                        MAX_ORES = 10 # A healthy, rich amount for the cave
                        
                        # If we need more ores, aggressively search for wall spots
                        if len(active_ores) < MAX_ORES:
                            for _ in range(20): # Try 20 random spots per frame
                                # Search in a doughnut shape (off-screen but nearby)
                                sign_x = random.choice([-1, 1])
                                sign_y = random.choice([-1, 1])
                                test_x = self.player.rect.centerx + sign_x * random.randint(300, 1100)
                                test_y = self.player.rect.centery + sign_y * random.randint(300, 1100)
                                
                                cx, cy = int(test_x // (CHUNK_SIZE * TILE_SIZE)), int(test_y // (CHUNK_SIZE * TILE_SIZE))
                                
                                if (cx, cy) in self.world.cave_chunks:
                                    chunk = self.world.cave_chunks[(cx, cy)]
                                    lx, ly = int((test_x % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE), int((test_y % (CHUNK_SIZE * TILE_SIZE)) // TILE_SIZE)
                                    
                                    # Rule 1: Must be open cave floor
                                    if 0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE and chunk.grid[lx][ly] not in COLLISION_TILES:
                                        
                                        # Rule 2: Must touch a black cave wall
                                        wall_neighbor = False
                                        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                                            if 0 <= lx+dx < CHUNK_SIZE and 0 <= ly+dy < CHUNK_SIZE:
                                                if chunk.grid[lx+dx][ly+dy] == BIOME_CAVE_WALL:
                                                    wall_neighbor = True; break
                                        
                                        if wall_neighbor:
                                            world_px = (cx * CHUNK_SIZE + lx) * TILE_SIZE
                                            world_py = (cy * CHUNK_SIZE + ly) * TILE_SIZE
                                            
                                            # Avoid overlapping portals and other ores
                                            overlap_portal = any(p.rect.x == world_px and p.rect.y == world_py for p in self.world.active_portals)
                                            overlap_ore = any(abs(e.rect.x - world_px) < TILE_SIZE for e in active_ores)
                                            
                                            if not overlap_portal and not overlap_ore:
                                                new_ore = GlyphOre(world_px + TILE_SIZE//2, world_py + TILE_SIZE//2)
                                                self.enemies.append(new_ore)
                                                active_ores.append(new_ore)
                                                break # Successfully spawned one this frame

                    # 2. MONSTER RECYCLING & ORE DESPAWNING
                    for e in self.enemies:
                        vec_to_player = Vector2(self.player.rect.center) - Vector2(e.rect.center)
                        
                        if getattr(e, 'is_ore', False):
                            if vec_to_player.length() > DESPAWN_DISTANCE + 200: e.is_alive = False
                            else: e.update(dt, self.player, nearby_walls, self.texts, self.camera)
                            continue
                            
                        # Standard Monster Teleport Recycler
                        if vec_to_player.length() > DESPAWN_DISTANCE:
                            found_safe_spot = False
                            safe_x, safe_y = 0, 0
                            
                            for _ in range(10):
                                test_x = self.player.rect.centerx + random.choice([-1, 1]) * random.randint(SPAWN_MIN, SPAWN_MAX)
                                test_y = self.player.rect.centery + random.choice([-1, 1]) * random.randint(SPAWN_MIN, SPAWN_MAX)
                                test_rect = pygame.Rect(test_x - 13, test_y - 13, 26, 26)
                                if not self.world.get_nearby_walls(test_rect):
                                    safe_x, safe_y = test_x, test_y
                                    found_safe_spot = True
                                    break 
                                    
                            # ONLY teleport if a valid off-screen spot was actually found
                            if found_safe_spot:
                                e.rect.centerx = safe_x
                                e.rect.centery = safe_y
                                e.stats.current_hp = e.stats.max_hp
                                e.state = ENEMY_CHASING
                                e.velocity = Vector2(0, 0)
                        else:
                            e.update(dt, self.player, nearby_walls, self.texts, self.camera)
                            
                    self.enemies = [e for e in self.enemies if e.is_alive]
                    
                    for drop in self.loot_drops[:]:
                        if drop.update(dt, self.player): 
                            if self.player.inventory.add_item(drop.item):
                                self.texts.add(self.player.rect.centerx, self.player.rect.top, f"+ {drop.item.name}", drop.item.color)
                            self.loot_drops.remove(drop)

                    self.texts.update(dt)

                # Camera follows player
                try:
                    self.camera.update(self.player, dt)
                except TypeError:
                    self.camera.update(self.player)

                # --- Drawing Phase ---
                bg_color = BIOME_COLORS.get(BIOME_OCEAN, (30, 30, 30))
                if getattr(self.world, 'current_layer', 0) == -1:
                    bg_color = BIOME_COLORS.get(BIOME_CAVE_WALL, (10, 10, 15))
                self.screen.fill(bg_color) 
                
                # Draw Procedural Map First
                self.world.draw_visible_chunks(self.screen, self.camera)
                
                # Draw Entities & HUD
                for drop in self.loot_drops: drop.draw(self.screen, self.camera)
                for e in self.enemies: e.draw(self.screen, self.camera)
                self.player.draw(self.screen, self.camera)
                self.texts.draw(self.screen, self.camera)
                self.hud.draw(self.screen, self.player, self.hex_ui)
                self.debug.draw(self.screen, len(self.enemies))
                
                # Draw UI Transitions Over Everything
                if self.transition_state == "IN":
                    t = self.ease_out_quart(self.transition_progress)
                    dir_vec = self.menu_transitions[self.next_menu]
                    offset_x, offset_y = dir_vec.x * WIDTH, dir_vec.y * HEIGHT
                    push_offset = Vector2(offset_x * t, offset_y * t)
                    self.draw_hub_menu(push_offset)
                    menu_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    self._draw_specific_menu(self.next_menu, menu_surf)
                    start_pos = Vector2(-offset_x, -offset_y)
                    current_pos = start_pos.lerp(Vector2(0,0), t)
                    self.screen.blit(menu_surf, current_pos)
                    
                elif self.transition_state == "OUT":
                    t = self.ease_out_quart(self.transition_progress)
                    dir_vec = self.menu_transitions[self.active_menu]
                    offset_x, offset_y = dir_vec.x * WIDTH, dir_vec.y * HEIGHT
                    push_offset = Vector2(offset_x * (1.0 - t), offset_y * (1.0 - t))
                    self.draw_hub_menu(push_offset)
                    menu_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    self._draw_specific_menu(self.active_menu, menu_surf)
                    end_pos = Vector2(-offset_x, -offset_y)
                    current_pos = Vector2(0,0).lerp(end_pos, t)
                    self.screen.blit(menu_surf, current_pos)
                    
                else:
                    if self.active_menu == "HUB": self.draw_hub_menu()
                    elif self.active_menu is not None: self._draw_specific_menu(self.active_menu, self.screen)
                
                pygame.display.flip()

            except SystemError as e:
                print(f"\n[FATAL DRIVER ERROR] {e}\nRebooting Input Module...")
                pygame.joystick.quit()
                pygame.joystick.init()
                if hasattr(self.player, 'input'):
                    self.player.input._scan_controllers()
            except Exception as e:
                print(f"\n[INTERNAL ERROR] {e}")
                traceback.print_exc()

if __name__ == "__main__":
    game = Game()
    game.run()