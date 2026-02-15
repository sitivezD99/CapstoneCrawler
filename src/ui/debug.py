# src/ui/debug.py
import pygame
from settings import TILE_SIZE, CHUNK_SIZE

class DebugInterface:
    def __init__(self, player, dungeon, clock):
        self.player = player
        self.dungeon = dungeon
        self.clock = clock
        self.font = pygame.font.SysFont("Consolas", 14)
        self.active = False 

    def toggle(self):
        self.active = not self.active

    def draw(self, screen, enemy_count=0): # Added parameter
        if not self.active: return

        # Semi-transparent background
        bg = pygame.Surface((300, 150))
        bg.set_alpha(180)
        bg.fill((0, 0, 0))
        screen.blit(bg, (10, 80))

        lines = [
            f"FPS: {int(self.clock.get_fps())}",
            f"World Pos: {int(self.player.rect.x)}, {int(self.player.rect.y)}",
            f"Chunk Pos: {int(self.player.rect.x // (CHUNK_SIZE * TILE_SIZE))}, {int(self.player.rect.y // (CHUNK_SIZE * TILE_SIZE))}",
            f"Loaded Chunks: {len(self.dungeon.chunks)}",
            f"Active Enemies: {enemy_count}" # Now shows real number!
        ]

        for i, line in enumerate(lines):
            text = self.font.render(line, True, (0, 255, 0))
            screen.blit(text, (20, 90 + (i * 20)))