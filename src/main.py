# src/main.py
import pygame
import sys
from pygame.math import Vector2
from settings import *
from world.dungeon import DungeonManager
from world.player import Player, STATE_ATTACKING
from world.spawner import Spawner
from engine.camera import Camera
from ui.hud import HUD
from ui.debug import DebugInterface

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Capstone Phase 4: Law of the Cavern")
        self.clock = pygame.time.Clock()

        self.dungeon = DungeonManager()
        self.camera = Camera(WIDTH, HEIGHT)
        
        spawn_x, spawn_y = self.find_valid_spawn(0, 0)
        self.player = Player(spawn_x, spawn_y)
        
        self.enemies = [] 
        self.room_cooldowns = {} 
        self.current_room_id = None
        
        # --- LAW OF THE TIMER ---
        self.respawn_time = 10 * 60 * 1000 # 10 Minutes

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

    def get_player_room_id(self):
        # Uses the Grid System to check "Potential" rooms
        px_tile = self.player.rect.centerx // TILE_SIZE
        py_tile = self.player.rect.centery // TILE_SIZE
        gx = px_tile // ROOM_GRID_SIZE
        gy = py_tile // ROOM_GRID_SIZE
        gen = self.dungeon.generator
        if gen.get_pseudo_random(gx, gy, "exist") < ROOM_CHANCE:
            return (gx, gy)
        return None

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0 
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F3: self.debug.toggle()

            self.enemies = [e for e in self.enemies if e.is_alive]

            # --- SPAWN LOGIC ---
            new_room_id = self.get_player_room_id()

            # If we entered a potentially valid room grid...
            if new_room_id is not None:
                # Check 1: Is it the same room we are already fighting in?
                if new_room_id != self.current_room_id:
                    
                    # Check 2: Is it on Cooldown?
                    ready_time = self.room_cooldowns.get(new_room_id, 0)
                    if current_time >= ready_time:
                        
                        # TRY TO SPAWN
                        tile_x = int(self.player.rect.centerx // TILE_SIZE)
                        tile_y = int(self.player.rect.centery // TILE_SIZE)
                        
                        new_wave = Spawner.spawn_wave(self.dungeon, tile_x, tile_y)
                        
                        if new_wave:
                            # SUCCESS: We are in a real room (not a tunnel)
                            print(f"New Room Entered {new_room_id}. Spawning Wave.")
                            self.enemies.extend(new_wave)
                            self.current_room_id = new_room_id
                            
                            # START 10 MINUTE TIMER
                            self.room_cooldowns[new_room_id] = current_time + self.respawn_time
                        else:
                            # FAIL: We are in a tunnel connecting to the room.
                            # Do NOT set ID, Do NOT set Cooldown.
                            # Just wait until player walks further in.
                            pass

            # Update & Draw
            nearby_walls = self.dungeon.get_nearby_walls(self.player.rect)
            
            if self.player.state == STATE_ATTACKING:
                killed = self.player.update_attack(dt, nearby_walls, self.enemies)
                if killed:
                    for e in killed: self.player.stats.gain_xp(50) 
            else:
                self.player.update(dt, nearby_walls)

            self.camera.update(self.player)

            for enemy in self.enemies:
                if Vector2(enemy.rect.center).distance_to(self.player.rect.center) > 2000:
                    enemy.is_alive = False 
                else:
                    enemy.update(dt, self.player, self.dungeon, self.enemies)

            self.screen.fill((20, 15, 25))
            self.dungeon.draw_visible_chunks(self.screen, self.camera)
            self.player.draw(self.screen, self.camera)
            for enemy in self.enemies: enemy.draw(self.screen, self.camera)
            self.hud.draw(self.screen)
            self.debug.draw(self.screen, len(self.enemies))

            pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()