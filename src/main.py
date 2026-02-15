import pygame
import sys
from settings import *
from world.dungeon import DungeonManager
from world.player import Player
from engine.camera import Camera

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Capstone Phase 1: Infinite Noise")
        self.clock = pygame.time.Clock()

        # Initialize Systems
        self.dungeon = DungeonManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Find a valid spawn point (Don't spawn in a wall!)
        spawn_x, spawn_y = 0, 0
        found = False
        # Simple search for a floor tile near 0,0
        for r in range(100):
            if self.dungeon.generator.get_tile_at(r, r) == 1:
                spawn_x, spawn_y = r * TILE_SIZE, r * TILE_SIZE
                found = True
                break
        
        self.player = Player(spawn_x, spawn_y)

    def run(self):
        while True:
            # 1. Event Loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # 2. Update
            # Only get walls near the player for physics (Optimization)
            nearby_walls = self.dungeon.get_nearby_walls(self.player.rect)
            self.player.update(nearby_walls)
            self.camera.update(self.player)

            # 3. Draw
            self.screen.fill((20, 10, 20)) # Dark Purple/Black BG
            
            # Draw World (Only visible chunks)
            self.dungeon.draw_visible_chunks(self.screen, self.camera)
            
            # Draw Player
            self.player.draw(self.screen, self.camera)
            
            # Debug Info
            pygame.display.set_caption(f"FPS: {int(self.clock.get_fps())} | Pos: {self.player.rect.center}")

            pygame.display.flip()
            self.clock.tick(FPS)