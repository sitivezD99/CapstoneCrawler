# src/engine/input.py
import pygame
from pygame.math import Vector2

class InputManager:
    def __init__(self):
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
        self.controller = None
        
        if self.joysticks:
            self.controller = self.joysticks[0]
            self.controller.init()
            print(f"Controller Detected: {self.controller.get_name()}")
        else:
            print("No Controller Detected. Using Keyboard.")

    def get_movement_vector(self):
        """Returns a normalized Vector2 (-1.0 to 1.0) representing move direction."""
        move = Vector2(0, 0)
        
        # 1. Keyboard Input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:  move.x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:    move.y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  move.y += 1

        # Normalize Keyboard (prevent fast diagonals)
        if move.length() > 0:
            move = move.normalize()

        # 2. Controller Input (Override if stick is pushed)
        if self.controller:
            # Axis 0 = Left Stick X, Axis 1 = Left Stick Y
            x_axis = self.controller.get_axis(0)
            y_axis = self.controller.get_axis(1)
            
            # Deadzone Check (0.2)
            if abs(x_axis) < 0.2: x_axis = 0
            if abs(y_axis) < 0.2: y_axis = 0
            
            stick_input = Vector2(x_axis, y_axis)
            if stick_input.length() > 0.2:
                move = stick_input # Analog control (variable speed)

        return move

    def is_action_pressed(self, action="attack"):
        """Checks for 'attack' or 'dash' inputs."""
        keys = pygame.key.get_pressed()
        
        if action == "attack":
            # Space or Controller Button 0 (A/Cross)
            if keys[pygame.K_SPACE]: return True
            if self.controller and self.controller.get_button(0): return True
            
        elif action == "dash":
            # Shift or Controller Button 1 (B/Circle)
            if keys[pygame.K_LSHIFT]: return True
            if self.controller and self.controller.get_button(1): return True
            
        return False