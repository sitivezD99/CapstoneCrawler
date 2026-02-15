# src/world/player.py
import pygame
from pygame.math import Vector2
from settings import *
from engine.entity import Entity

STATE_IDLE = "IDLE"
STATE_MOVING = "MOVING"
STATE_ATTACKING = "ATTACKING"
STATE_COOLDOWN = "COOLDOWN"

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 0, 255))
        self.state = STATE_IDLE
        self.state_timer = 0
        self.facing_direction = Vector2(0, 1)
        self.attack_hitbox = None

    def update(self, dt, walls):
        # Standard update does not handle combat anymore, main.py does
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

        keys = pygame.key.get_pressed()
        accel = Vector2(0, 0)
        
        if keys[pygame.K_LEFT]:  accel.x = -1
        if keys[pygame.K_RIGHT]: accel.x = 1
        if keys[pygame.K_UP]:    accel.y = -1
        if keys[pygame.K_DOWN]:  accel.y = 1

        if accel.length() > 0:
            accel = accel.normalize()
            self.facing_direction = accel
            self.state = STATE_MOVING
        else:
            self.state = STATE_IDLE

        accel *= self.stats.speed
        self.velocity += accel
        self.velocity *= PLAYER_FRICTION
        
        if self.velocity.length() > PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(PLAYER_MAX_SPEED)

        if keys[pygame.K_SPACE]:
            self.start_attack()

    def start_attack(self):
        self.state = STATE_ATTACKING
        self.state_timer = ATTACK_DURATION
        attack_x = self.rect.centerx + (self.facing_direction.x * 20) - (TILE_SIZE // 2)
        attack_y = self.rect.centery + (self.facing_direction.y * 20) - (TILE_SIZE // 2)
        self.attack_hitbox = pygame.Rect(attack_x, attack_y, TILE_SIZE, TILE_SIZE)

    def update_attack(self, dt, walls, enemies):
        """Returns list of killed enemies"""
        self.state_timer -= dt
        killed = []
        
        if self.attack_hitbox:
            # Walls
            for wall in walls:
                if self.attack_hitbox.colliderect(wall):
                    self.attack_hitbox = None
                    return []

            # Enemies
            for enemy in enemies:
                if self.attack_hitbox.colliderect(enemy.rect):
                    if enemy.is_alive:
                        print("SMACK!")
                        enemy.stats.modify_hp(-self.stats.damage)
                        
                        # Knockback
                        knock = (Vector2(enemy.rect.center) - Vector2(self.rect.center))
                        if knock.length() > 0:
                            enemy.velocity += knock.normalize() * 10 
                        
                        if enemy.stats.current_hp <= 0:
                            enemy.is_alive = False
                            killed.append(enemy)
                            
                        self.attack_hitbox = None
                        return killed
        
        if self.state_timer <= 0:
            self.state = STATE_COOLDOWN
            self.state_timer = ATTACK_COOLDOWN
            self.attack_hitbox = None
            
        return killed

    def draw(self, screen, camera):
        if self.state == STATE_MOVING: self.color = (255, 0, 0)
        elif self.state == STATE_ATTACKING: self.color = (255, 215, 0)
        elif self.state == STATE_COOLDOWN: self.color = (100, 100, 100)
        else: self.color = (0, 0, 255)
        
        super().draw(screen, camera)
        
        if self.state == STATE_ATTACKING and self.attack_hitbox:
            hit_rect = camera.apply(self.attack_hitbox)
            pygame.draw.rect(screen, (255, 255, 255), hit_rect, 2)