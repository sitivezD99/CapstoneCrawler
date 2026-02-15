# src/main.py
import pygame
import sys
import random
from pygame.math import Vector2
from settings import *
from world.dungeon import DungeonManager
from world.player import Player, STATE_ATTACKING
from world.enemy import Enemy
from engine.camera import Camera
from ui.hud import HUD
from ui.debug import DebugInterface

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Capstone Phase 3.5: Bug Fixes")
        self.clock = pygame.time.Clock()

        self.dungeon = DungeonManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        spawn_x, spawn_y = self.find_valid_spawn(0, 0)
        self.player = Player(spawn_x, spawn_y)
        
        self.enemies = [] 
        self.spawn_timer = 0
        self.spawn_enemy_near_player()

        self.hud = HUD(self.player)
        self.debug = DebugInterface(self.player, self.dungeon, self.clock)

    def find_valid_spawn(self, start_cx, start_cy):
        gen = self.dungeon.generator
        for radius in range(0, 10):
            for cy in range(-radius, radius + 1):
                for cx in range(-radius, radius + 1):
                    if gen.get_pseudo_random(cx, cy, "exist") < ROOM_CHANCE:
                        jitter_x = int(gen.get_pseudo_random(cx, cy, "jx") * (ROOM_GRID_SIZE - 2 * ROOM_MAX_RADIUS))
                        jitter_y = int(gen.get_pseudo_random(cx, cy, "jy") * (ROOM_GRID_SIZE - 2 * ROOM_MAX_RADIUS))
                        cx_tile = (cx * ROOM_GRID_SIZE) + ROOM_MAX_RADIUS + jitter_x
                        cy_tile = (cy * ROOM_GRID_SIZE) + ROOM_MAX_RADIUS + jitter_y
                        return cx_tile * TILE_SIZE, cy_tile * TILE_SIZE
        return 0, 0 

    def spawn_enemy_near_player(self):
        for _ in range(10):
            angle = random.uniform(0, 6.28)
            dist = random.uniform(300, 600)
            offset = Vector2(dist, 0).rotate_rad(angle)
            spawn_pos = Vector2(self.player.rect.center) + offset
            
            gx = int(spawn_pos.x // TILE_SIZE)
            gy = int(spawn_pos.y // TILE_SIZE)
            cx = gx // CHUNK_SIZE
            cy = gy // CHUNK_SIZE
            chunk = self.dungeon.get_chunk(cx, cy)
            
            lx = gx % CHUNK_SIZE
            ly = gy % CHUNK_SIZE
            
            if chunk.grid[ly][lx] == 1:
                new_enemy = Enemy(spawn_pos.x, spawn_pos.y)
                self.enemies.append(new_enemy)
                return 

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3: self.debug.toggle()

            # 1. Despawn Logic
            self.enemies = [
                e for e in self.enemies 
                if e.is_alive and Vector2(e.rect.center).distance_to(self.player.rect.center) < 1500
            ]
            
            # 2. Spawn Logic
            if len(self.enemies) < 6:
                self.spawn_timer += dt
                if self.spawn_timer > 1.5: 
                    self.spawn_enemy_near_player()
                    self.spawn_timer = 0

            # 3. Update World
            nearby_walls = self.dungeon.get_nearby_walls(self.player.rect)
            
            if self.player.state == STATE_ATTACKING:
                # Capture the killed enemies list!
                killed_enemies = self.player.update_attack(dt, nearby_walls, self.enemies)
                if killed_enemies:
                    for e in killed_enemies:
                        self.player.stats.gain_xp(50) # Award 50 XP per kill
            else:
                self.player.update(dt, nearby_walls)

            self.camera.update(self.player)

            for enemy in self.enemies:
                enemy.update(dt, self.player, self.dungeon)

            # 4. Draw
            self.screen.fill((20, 15, 25))
            self.dungeon.draw_visible_chunks(self.screen, self.camera)
            self.player.draw(self.screen, self.camera)
            
            for enemy in self.enemies:
                enemy.draw(self.screen, self.camera)
            
            self.hud.draw(self.screen)
            self.debug.draw(self.screen, len(self.enemies))

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()