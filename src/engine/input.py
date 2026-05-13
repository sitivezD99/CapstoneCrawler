# src/engine/input.py
import pygame
from pygame.math import Vector2

class InputManager:
    def __init__(self):
        pygame.joystick.init()
        self.joystick = None
        self._scan_controllers()

    def _scan_controllers(self):
        # Only take the first controller and ignore duplicates
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

    def handle_hotplug(self, event):
        if event.type == pygame.JOYDEVICEADDED:
            if not self.joystick: self._scan_controllers()
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.joystick = None

    def get_movement_vector(self):
        vec = Vector2(0, 0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]: vec.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: vec.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: vec.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: vec.x += 1

        if self.joystick:
            jx = self.joystick.get_axis(0)
            jy = self.joystick.get_axis(1)
            if abs(jx) > 0.15: vec.x = jx
            if abs(jy) > 0.15: vec.y = jy
        return vec.normalize() if vec.length() > 0 else vec

    def get_aim_vector(self):
        """Returns the direction for skills (Right Stick or Mouse)"""
        vec = Vector2(0, 0)
        
        # 1. Check Controller Right Stick (Axes 2 and 3)
        if self.joystick:
            rx = self.joystick.get_axis(2)
            ry = self.joystick.get_axis(3)
            if abs(rx) > 0.2 or abs(ry) > 0.2:
                vec.x = rx
                vec.y = ry

        return vec

    # --- ACTION BUTTONS ---

    def is_attack_pressed(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]: return True
        if self.joystick and self.joystick.get_button(0): return True # A
        return False

    def is_dash_pressed(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT]: return True
        if self.joystick and self.joystick.get_button(5): return True # B
        return False

    def is_skill_1_pressed(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_x]: return True
        if self.joystick and self.joystick.get_button(2): return True # X
        return False

    def is_skill_2_pressed(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_y]: return True
        if self.joystick and self.joystick.get_button(3): return True # Y
        return False

    def is_skill_3_pressed(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_b]: return True
        if self.joystick and self.joystick.get_button(1): return True # RB
        return False

    def is_menu_pressed(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE] or keys[pygame.K_TAB]: return True
        if self.joystick and self.joystick.get_button(7): return True # Start
        return False

    def is_inventory_pressed(self, event=None):
        if event and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_i: return True
        if event and event.type == pygame.JOYBUTTONDOWN:
            if event.button == 6: return True # Back/Select
        return False