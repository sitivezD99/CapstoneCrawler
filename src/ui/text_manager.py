# src/ui/text_manager.py
import pygame
import random

class FloatingText:
    def __init__(self, x, y, text, color=(255, 50, 50)):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life_timer = 1.0 # Seconds to live
        self.velocity_y = -30 # Pixels per second (drift up)
        self.alpha = 255
        
        # Simple default font
        self.font = pygame.font.Font(None, 24)

    def update(self, dt):
        self.life_timer -= dt
        self.y += self.velocity_y * dt
        
        # Fade out effect logic
        if self.life_timer < 0.5:
            self.alpha = max(0, int(255 * (self.life_timer / 0.5)))

    def draw(self, screen, camera):
        # Render text
        surf = self.font.render(self.text, True, self.color)
        surf.set_alpha(self.alpha)
        
        # Apply camera offset
        rect = surf.get_rect(center=(self.x, self.y))
        draw_rect = camera.apply(rect)
        
        screen.blit(surf, draw_rect)

class TextManager:
    def __init__(self):
        self.texts = []

    def add(self, x, y, text, color=(255, 50, 50)):
        # Add slight random offset so numbers don't stack perfectly on top of each other
        off_x = random.randint(-10, 10)
        off_y = random.randint(-10, 10)
        self.texts.append(FloatingText(x + off_x, y + off_y, text, color))

    def update(self, dt):
        for text in self.texts:
            text.update(dt)
        self.texts = [t for t in self.texts if t.life_timer > 0]

    def draw(self, screen, camera):
        for text in self.texts:
            text.draw(screen, camera)