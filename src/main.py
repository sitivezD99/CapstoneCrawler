# src/main.py
import pygame
import sys
from settings import *

from world.universe import UniverseManager 
from world.player import Player, STATE_ATTACKING
from world.spawner import Spawner 
from engine.camera import Camera
from ui.hud import HUD
from ui.debug import DebugInterface
from ui.text_manager import TextManager

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Shattered Atlas: Infinite World")
        self.clock = pygame.time.Clock()

        self.world = UniverseManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        print("Searching for land...")
        spawn_x, spawn_y = self.world.surface_generator.find_spawn_point()
        self.player = Player(spawn_x, spawn_y)
        print(f"Player spawned at {spawn_x}, {spawn_y}")
        
        self.enemies = [] 
        self.spawn_timer = 0
        
        self.hud = HUD(self.player)
        self.debug = DebugInterface(self.player, self.world, self.clock)
        self.text_manager = TextManager() 

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0 

            # --- INPUT SHIELD ---
            try:
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                        if hasattr(self.player, 'input'):
                            self.player.input.handle_hotplug(event)
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_F3: self.debug.toggle()
                        if event.key == pygame.K_g: self.world.toggle_layer()
            except KeyError: pass 

            # --- GAME LOGIC ---
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                if len(self.enemies) < 10:
                    new_enemies = Spawner.spawn_enemies(self.world, self.player)
                    self.enemies.extend(new_enemies)
                self.spawn_timer = 2.0 

            nearby_walls = self.world.get_nearby_walls(self.player.rect)
            
            # Portals
            did_teleport = self.world.check_portals(self.player)
            if did_teleport:
                nearby_walls = self.world.get_nearby_walls(self.player.rect)
            
            # Enemies
            for enemy in self.enemies:
                if enemy.is_alive:
                    enemy.update(dt, self.player, self.world, self.enemies)
            self.enemies = [e for e in self.enemies if e.is_alive]

            # --- PLAYER UPDATE (THE FIX) ---
            # 1. Update Player Physics & Timers (Always run this!)
            self.player.update(dt, nearby_walls)
            
            # 2. Check Combat Collisions (Only if attacking)
            if self.player.state == STATE_ATTACKING:
                killed_enemies = self.player.check_attack_collisions(self.enemies, self.text_manager)
                if len(killed_enemies) > 0:
                    self.camera.trigger_shake(duration=10, magnitude=6)

            # Text & Camera
            self.text_manager.update(dt) 
            self.camera.update(self.player)

            # --- DRAW ---
            bg_color = BIOME_COLORS[BIOME_OCEAN]
            if self.world.current_layer == -1:
                bg_color = BIOME_COLORS[BIOME_CAVE_WALL]
                
            self.screen.fill(bg_color) 
            self.world.draw_visible_chunks(self.screen, self.camera)
            for enemy in self.enemies: enemy.draw(self.screen, self.camera)
            self.player.draw(self.screen, self.camera)
            self.hud.draw(self.screen)
            self.text_manager.draw(self.screen, self.camera)
            self.debug.draw(self.screen, len(self.enemies))

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()