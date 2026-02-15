# src/ui/debug.py
import pygame
from settings import TILE_SIZE, CHUNK_SIZE

class DebugInterface:
    def __init__(self, player, world, clock): # Renamed dungeon -> world
        self.player = player
        self.world = world
        self.clock = clock
        self.font = pygame.font.SysFont("Consolas", 14)
        self.active = False 

    def toggle(self):
        self.active = not self.active

    def draw(self, screen, enemy_count=0):
        if not self.active: return

        bg = pygame.Surface((300, 150))
        bg.set_alpha(180)
        bg.fill((0, 0, 0))
        screen.blit(bg, (10, 80))

        lines = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Pos: {int(self.player.rect.x)}, {int(self.player.rect.y)}",
            # Updated to use self.world.chunks
            f"Loaded Chunks: {len(self.world.chunks)}",
            f"Biome ID: N/A" # Placeholder
        ]

        for i, line in enumerate(lines):
            text = self.font.render(line, True, (0, 255, 0))
            screen.blit(text, (20, 90 + (i * 20)))