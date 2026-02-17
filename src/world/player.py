# src/world/player.py
import pygame
from pygame.math import Vector2
from settings import *
from engine.entity import Entity
from engine.physics import move_and_slide
from engine.input import InputManager

STATE_IDLE = "IDLE"
STATE_MOVING = "MOVING"
STATE_ATTACKING = "ATTACKING"
STATE_DASHING = "DASHING"
STATE_COOLDOWN = "COOLDOWN"

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (0, 0, 255))
        self.input = InputManager()
        self.state = STATE_IDLE
        self.state_timer = 0
        
        # Stats
        self.level = 1
        self.xp = 0
        self.xp_next_level = 100
        self.stats.speed = 1.0 
        
        # Vectors
        self.aim_direction = Vector2(0, 1) 
        self.move_direction = Vector2(0, 0)
        self.dash_direction = Vector2(0, 0)
        
        # Combat
        self.attack_hitbox = None
        self.enemies_hit = set()
        
        # Dash Settings
        self.dash_cooldown_timer = 0
        self.dash_duration = 0.2
        self.dash_speed_mult = 3.0
        self.dash_cooldown = 1.0

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_next_level:
            self.level_up()

    def level_up(self):
        self.xp -= self.xp_next_level
        self.level += 1
        self.xp_next_level = int(self.xp_next_level * 1.5)
        self.stats.max_hp += 10
        self.stats.current_hp = self.stats.max_hp 
        self.stats.damage += 2
        print(f"🎉 LEVEL UP! Level {self.level}")

    def update(self, dt, walls):
        """Runs EVERY frame. Handles Input, Physics, and Timers."""
        
        # 1. Input & Movement Logic
        self.handle_input(dt)
        self.apply_physics(walls)
        
        # 2. Manage Dash Cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

        # 3. Manage State Timers (The Fix!)
        if self.state_timer > 0:
            self.state_timer -= dt
            
            # State Transitions when timer ends
            if self.state_timer <= 0:
                if self.state == STATE_ATTACKING:
                    self.state = STATE_COOLDOWN
                    self.state_timer = ATTACK_COOLDOWN
                    self.attack_hitbox = None
                
                elif self.state == STATE_DASHING:
                    self.state = STATE_IDLE
                    
                elif self.state == STATE_COOLDOWN:
                    self.state = STATE_IDLE

    def handle_input(self, dt):
        # 1. Get raw input
        self.move_direction = self.input.get_movement_vector()
        aim_input = self.input.get_aim_vector()
        
        # 2. Update Aim Direction
        if aim_input.length() > 0:
            self.aim_direction = aim_input.normalize()
        elif self.move_direction.length() > 0:
            self.aim_direction = self.move_direction.normalize()

        base_speed = self.stats.speed * PLAYER_MAX_SPEED
        
        # --- STATE MACHINE MOVEMENT ---
        
        # PRIORITY 1: Dashing (Locks movement)
        if self.state == STATE_DASHING:
            self.velocity = self.dash_direction * (base_speed * self.dash_speed_mult)
            return 

        # PRIORITY 2: Attacking (Allows slow movement)
        if self.state == STATE_ATTACKING:
            target_velocity = self.move_direction * (base_speed * 0.5)
            self.velocity = self.velocity.lerp(target_velocity, 0.2)
            # Do NOT return here, we still want to check for new inputs (buffered)

        # PRIORITY 3: Normal Movement
        elif self.state != STATE_DASHING:
            target_velocity = self.move_direction * base_speed
            self.velocity = self.velocity.lerp(target_velocity, 0.2)
            
            # Visual State Update
            if self.state != STATE_COOLDOWN:
                if self.move_direction.length() > 0:
                    self.state = STATE_MOVING
                else:
                    self.state = STATE_IDLE

        # --- ACTION CHECKS ---
        if self.input.is_dash_pressed() and self.dash_cooldown_timer <= 0 and self.state != STATE_DASHING:
            self.start_dash()
            
        elif self.input.is_attack_pressed() and self.state != STATE_COOLDOWN and self.state != STATE_ATTACKING and self.state != STATE_DASHING:
            self.start_attack()

    def start_dash(self):
        self.state = STATE_DASHING
        self.state_timer = self.dash_duration
        self.dash_cooldown_timer = self.dash_cooldown
        
        if self.move_direction.length() > 0:
            self.dash_direction = self.move_direction.normalize()
        else:
            self.dash_direction = self.aim_direction.normalize()

    def start_attack(self):
        self.state = STATE_ATTACKING
        self.state_timer = ATTACK_DURATION
        self.enemies_hit.clear()
        
        offset_dist = TILE_SIZE * 0.8
        attack_x = self.rect.centerx + (self.aim_direction.x * offset_dist) - (TILE_SIZE // 2)
        attack_y = self.rect.centery + (self.aim_direction.y * offset_dist) - (TILE_SIZE // 2)
        self.attack_hitbox = pygame.Rect(attack_x, attack_y, TILE_SIZE, TILE_SIZE)

    def check_attack_collisions(self, enemies, text_manager):
        """Only handles damage calculation. Called from Main."""
        killed = []
        
        if self.state == STATE_ATTACKING and self.attack_hitbox:
            # Sync hitbox
            offset_dist = TILE_SIZE * 0.8
            self.attack_hitbox.centerx = self.rect.centerx + (self.aim_direction.x * offset_dist)
            self.attack_hitbox.centery = self.rect.centery + (self.aim_direction.y * offset_dist)

            for enemy in enemies:
                if self.attack_hitbox.colliderect(enemy.rect) and enemy not in self.enemies_hit:
                    if enemy.is_alive:
                        self.enemies_hit.add(enemy)
                        
                        dmg = self.stats.damage
                        enemy.stats.modify_hp(-dmg)
                        text_manager.add(enemy.rect.centerx, enemy.rect.top, f"-{dmg}", (255, 255, 255))
                        
                        enemy.velocity += self.aim_direction * 20
                        
                        if enemy.stats.current_hp <= 0:
                            enemy.is_alive = False
                            killed.append(enemy)
                            self.gain_xp(25)
                
        return killed

    def apply_physics(self, walls):
        self.rect = move_and_slide(self.rect, self.velocity, walls)

    def draw(self, screen, camera):
        # Visual State Machine
        if self.state == STATE_DASHING:
            self.color = (0, 255, 255)   # CYAN
        elif self.state == STATE_ATTACKING: 
            self.color = (255, 215, 0)   # GOLD
        elif self.state == STATE_COOLDOWN: 
            self.color = (100, 100, 100) # GREY
        elif self.state == STATE_MOVING:   
            self.color = (255, 50, 50)   # RED
        else: 
            self.color = (50, 50, 255)   # BLUE
        
        super().draw(screen, camera)
        
        # Aim Line
        start_pos = camera.apply(self.rect).center
        end_pos = (start_pos[0] + self.aim_direction.x * 40, start_pos[1] + self.aim_direction.y * 40)
        pygame.draw.line(screen, (255, 0, 0), start_pos, end_pos, 2)

        # Dash Bar
        if self.dash_cooldown_timer > 0:
            pct = 1.0 - (self.dash_cooldown_timer / self.dash_cooldown)
            bar_rect = camera.apply(self.rect)
            bar_y = bar_rect.bottom + 4
            pygame.draw.rect(screen, (50, 50, 50), (bar_rect.x, bar_y, TILE_SIZE, 3))
            pygame.draw.rect(screen, (0, 255, 255), (bar_rect.x, bar_y, TILE_SIZE * pct, 3))

        # Debug Hitbox
        if self.state == STATE_ATTACKING and self.attack_hitbox:
            hit_rect = camera.apply(self.attack_hitbox)
            pygame.draw.rect(screen, (255, 255, 255), hit_rect, 2)