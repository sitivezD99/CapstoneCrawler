# src/main.py
import pygame
import sys
import random
from settings import *
from world.world import WorldManager 
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

        # Initialize World
        self.world = WorldManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Spawn Player on Land
        print("Searching for land...")
        spawn_x, spawn_y = self.world.generator.find_spawn_point()
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

            # --- SPAWNER LOGIC ---
            # Try to spawn an enemy every 2 seconds
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                # Keep population under control (Max 10 enemies active)
                if len(self.enemies) < 10:
                    new_enemies = Spawner.spawn_enemies(self.world, self.player)
                    self.enemies.extend(new_enemies)
                self.spawn_timer = 2.0 # Reset timer

            # --- UPDATE ---
            nearby_walls = self.world.get_nearby_walls(self.player.rect)
            
            # Update Enemies
            for enemy in self.enemies:
                if enemy.is_alive:
                    enemy.update(dt, self.player, self.world, self.enemies)
            
            # Clean up dead enemies
            self.enemies = [e for e in self.enemies if e.is_alive]

            # Update Player
            if self.player.state == STATE_ATTACKING:
                self.player.update_attack(dt, nearby_walls, self.enemies)
            else:
                self.player.update(dt, nearby_walls)

            self.camera.update(self.player)

            # --- DRAW ---
            self.screen.fill(BIOME_COLORS[BIOME_OCEAN]) # Background
            
            self.world.draw_visible_chunks(self.screen, self.camera)
            
            # --- VISIBILITY FIX IS HERE ---
            # We removed the 'if colliderect' check. 
            # Now we just draw every living enemy. 
            # The Camera class handles the positioning math automatically.
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)
                    
            self.player.draw(self.screen, self.camera)
            
            self.hud.draw(self.screen)
            self.debug.draw(self.screen, len(self.enemies))

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()