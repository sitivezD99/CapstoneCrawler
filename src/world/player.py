# src/world/player.py
import pygame
from pygame.math import Vector2
from settings import *
from engine.entity import Entity
from engine.physics import move_and_slide
from engine.input import InputManager # <--- New Import

STATE_IDLE = "IDLE"
STATE_MOVING = "MOVING"
STATE_ATTACKING = "ATTACKING"
STATE_COOLDOWN = "COOLDOWN"

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 0, 255))
        self.input = InputManager() # <--- Attach Input Manager
        self.state = STATE_IDLE
        self.state_timer = 0
        self.facing_direction = Vector2(0, 1)
        self.attack_hitbox = None

    def update(self, dt, walls):
        if self.state == STATE_COOLDOWN:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = STATE_IDLE
            else:
                self.apply_physics(walls)
                return

        self.handle_input(dt)
        self.apply_physics(walls)

    def handle_input(self, dt):
        if self.state == STATE_ATTACKING or self.state == STATE_COOLDOWN: return

        # 1. Get Analog Vector
        move_dir = self.input.get_movement_vector()
        
        # 2. State Management
        if move_dir.length() > 0:
            self.facing_direction = move_dir.normalize()
            self.state = STATE_MOVING
        else:
            self.state = STATE_IDLE

        # 3. Apply Velocity
        # move_dir is already 0.0 to 1.0, so it handles speed scaling automatically
        target_velocity = move_dir * self.stats.speed * PLAYER_MAX_SPEED
        
        # Smooth Acceleration (Juice)
        self.velocity = self.velocity.lerp(target_velocity, 0.2)
        
        # 4. Action Inputs
        if self.input.is_action_pressed("attack"):
            self.start_attack()

    def start_attack(self):
        self.state = STATE_ATTACKING
        self.state_timer = ATTACK_DURATION
        attack_x = self.rect.centerx + (self.facing_direction.x * 20) - (TILE_SIZE // 2)
        attack_y = self.rect.centery + (self.facing_direction.y * 20) - (TILE_SIZE // 2)
        self.attack_hitbox = pygame.Rect(attack_x, attack_y, TILE_SIZE, TILE_SIZE)

    def update_attack(self, dt, walls, enemies):
        """AOE Combat Logic"""
        self.state_timer -= dt
        killed = []
        
        if self.attack_hitbox:
            # Wall Hit
            for wall in walls:
                if self.attack_hitbox.colliderect(wall):
                    self.attack_hitbox = None
                    return []

            # Enemy Hit
            hit_happened = False
            for enemy in enemies:
                if self.attack_hitbox.colliderect(enemy.rect):
                    if enemy.is_alive:
                        hit_happened = True
                        enemy.stats.modify_hp(-self.stats.damage)
                        
                        knock = (Vector2(enemy.rect.center) - Vector2(self.rect.center))
                        if knock.length() > 0:
                            enemy.velocity += knock.normalize() * 15 # Stronger knockback
                        
                        if enemy.stats.current_hp <= 0:
                            enemy.is_alive = False
                            killed.append(enemy)

            if hit_happened:
                self.attack_hitbox = None 
        
        if self.state_timer <= 0:
            self.state = STATE_COOLDOWN
            self.state_timer = ATTACK_COOLDOWN
            self.attack_hitbox = None
            
        return killed

    def apply_physics(self, walls):
        # Use new Slide Physics
        self.rect = move_and_slide(self.rect, self.velocity, walls)

    # Draw remains the same...
    def draw(self, screen, camera):
        if self.state == STATE_MOVING: self.color = (255, 0, 0)
        elif self.state == STATE_ATTACKING: self.color = (255, 215, 0)
        elif self.state == STATE_COOLDOWN: self.color = (100, 100, 100)
        else: self.color = (0, 0, 255)
        super().draw(screen, camera)
        if self.state == STATE_ATTACKING and self.attack_hitbox:
            hit_rect = camera.apply(self.attack_hitbox)
            pygame.draw.rect(screen, (255, 255, 255), hit_rect, 2)