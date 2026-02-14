import pygame
import sys
from settings import * # Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Capstone Crawler - Phase 1")
clock = pygame.time.Clock()

def main():
    while True:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # 2. Drawing
        screen.fill(BLACK)
        
        # Test: Draw a white square in the center
        pygame.draw.rect(screen, WHITE, (WIDTH//2, HEIGHT//2, 50, 50))
        
        # 3. Update Display
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()