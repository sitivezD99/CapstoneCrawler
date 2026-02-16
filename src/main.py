# src/main.py
import pygame
import sys
import random
from settings import *

# --- IMPORT UNIVERSE MANAGER ---
from world.universe import UniverseManager 

from world.player import Player, STATE_ATTACKING
from world.spawner import Spawner 
from engine.camera import Camera
from ui.hud import HUD
from ui.debug import DebugInterface

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Shattered Atlas: Infinite World")
        self.clock = pygame.time.Clock()

        # Initialize UNIVERSE (Manages Surface + Caves)
        self.world = UniverseManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Spawn Player on Land
        # We ask the surface generator specifically
        print("Searching for land...")
        spawn_x, spawn_y = self.world.surface_generator.find_spawn_point()
        self.player = Player(spawn_x, spawn_y)
        print(f"Player spawned at {spawn_x}, {spawn_y}")
        
        # --- ENTITIES ---
        self.enemies = [] 
        self.spawn_timer = 0
        
        self.hud = HUD(self.player)
        self.debug = DebugInterface(self.player, self.world, self.clock)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3: self.debug.toggle()
                    
                    # DEBUG: Press 'G' to swap dimensions
                    if event.key == pygame.K_g:
                        self.world.toggle_layer()

            # --- SPAWNER LOGIC ---
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                if len(self.enemies) < 10:
                    new_enemies = Spawner.spawn_enemies(self.world, self.player)
                    self.enemies.extend(new_enemies)
                self.spawn_timer = 2.0 

            # --- UPDATE ---
            nearby_walls = self.world.get_nearby_walls(self.player.rect)
            
            for enemy in self.enemies:
                if enemy.is_alive:
                    enemy.update(dt, self.player, self.world, self.enemies)
            
            self.enemies = [e for e in self.enemies if e.is_alive]

            if self.player.state == STATE_ATTACKING:
                self.player.update_attack(dt, nearby_walls, self.enemies)
            else:
                self.player.update(dt, nearby_walls)

            self.camera.update(self.player)

            # --- DRAW ---
            # Blue background for surface, Black for caves
            bg_color = BIOME_COLORS[BIOME_OCEAN]
            if self.world.current_layer == -1:
                bg_color = BIOME_COLORS[BIOME_CAVE_WALL]
                
            self.screen.fill(bg_color) 
            
            self.world.draw_visible_chunks(self.screen, self.camera)
            
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)
                    
            self.player.draw(self.screen, self.camera)
            self.hud.draw(self.screen)
            self.debug.draw(self.screen, len(self.enemies))

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()