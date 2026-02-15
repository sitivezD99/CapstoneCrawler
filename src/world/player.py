import pygame
from pygame.math import Vector2
from settings import *
from engine.physics import move

class Player:
    def __init__(self, x, y):
        # Spawn player
        self.rect = pygame.Rect(x, y, TILE_SIZE - 2, TILE_SIZE - 2)
        self.velocity = Vector2(0, 0)
        self.color = (255, 100, 100) # Red

    def update(self, walls):
        # 1. Handle Input (Acceleration)
        keys = pygame.key.get_pressed()
        acceleration = Vector2(0, 0)
        
        if keys[pygame.K_LEFT]:  acceleration.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]: acceleration.x = PLAYER_SPEED
        if keys[pygame.K_UP]:    acceleration.y = -PLAYER_SPEED
        if keys[pygame.K_DOWN]:  acceleration.y = PLAYER_SPEED

        # 2. Apply Physics Math
        self.velocity += acceleration
        
        # Friction (The "Slide")
        self.velocity *= PLAYER_FRICTION

        # Cap Max Speed
        if self.velocity.length() > PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(PLAYER_MAX_SPEED)

        # Stop completely if very slow (prevent micro-sliding)
        if self.velocity.length() < 0.1:
            self.velocity = Vector2(0, 0)

        # 3. Move with Collision
        self.rect, collisions = move(self.rect, self.velocity, walls)

    def draw(self, screen, camera):
        # Draw player relative to camera
        draw_rect = camera.apply(self.rect)
        pygame.draw.rect(screen, self.color, draw_rect)