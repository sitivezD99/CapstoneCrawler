# src/main.py
import pygame
import sys
from settings import *
# Change Import: Use WorldManager instead of DungeonManager
from world.world import WorldManager 
from world.player import Player, STATE_ATTACKING
from engine.camera import Camera
from ui.hud import HUD
from ui.debug import DebugInterface

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Shattered Atlas: Island Prototype")
        self.clock = pygame.time.Clock()

        # Initialize the New World
        self.world = WorldManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Spawn Player on Land
        # We ask the generator to find a safe spot
        spawn_x, spawn_y = self.world.generator.find_spawn_point()
        self.player = Player(spawn_x, spawn_y)
        
        # --- MONSTERS DISABLED FOR TERRAIN REWORK ---
        self.enemies = [] 
        
        self.hud = HUD(self.player)
        # Pass world instead of dungeon to debug
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

            # Update
            # Get walls from the new World system
            nearby_walls = self.world.get_nearby_walls(self.player.rect)
            
            if self.player.state == STATE_ATTACKING:
                self.player.update_attack(dt, nearby_walls, self.enemies)
            else:
                self.player.update(dt, nearby_walls)

            self.camera.update(self.player)

            # Draw
            self.screen.fill((10, 10, 50)) # Deep Ocean Background
            self.world.draw_visible_chunks(self.screen, self.camera) # Draw Islands
            self.player.draw(self.screen, self.camera)
            
            self.hud.draw(self.screen)
            self.debug.draw(self.screen, 0) # 0 enemies for now

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()