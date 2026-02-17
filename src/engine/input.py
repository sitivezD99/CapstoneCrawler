# src/engine/input.py
import pygame
import math

class InputManager:
    def __init__(self):
        self.joysticks = {}
        # Stores the starting value of triggers to handle inverted hardware
        self.trigger_offsets = {} 
        self.init_joysticks()
        
    def init_joysticks(self):
        pygame.joystick.init()
        self.joysticks = {}
        for i in range(pygame.joystick.get_count()):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                jid = joy.get_instance_id() if hasattr(joy, "get_instance_id") else i
                self.joysticks[jid] = joy
                
                # Calibration: Record the 'resting' state of the triggers
                # We wait a tiny bit for the OS to report the first value
                pygame.event.pump() 
                self.trigger_offsets[jid] = {
                    'axis4': joy.get_axis(4), # Left Trigger
                    'axis5': joy.get_axis(5)  # Right Trigger
                }
                
                print(f"🎮 Controller Connected: {joy.get_name()}")
                print(f"🛠️ Calibration - RT Resting: {self.trigger_offsets[jid]['axis5']:.2f}")
            except Exception as e:
                print(f"⚠️ Error: {e}")

    def handle_hotplug(self, event):
        if event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
            self.init_joysticks()

    def get_movement_vector(self):
        vec = pygame.math.Vector2(0, 0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]: vec.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: vec.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: vec.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: vec.x += 1

        for joy in self.joysticks.values():
            try:
                x, y = joy.get_axis(0), joy.get_axis(1)
                if abs(x) > 0.2: vec.x += x
                if abs(y) > 0.2: vec.y += y
            except: pass
        if vec.length() > 1.0: vec = vec.normalize()
        return vec

    def get_aim_vector(self):
        vec = pygame.math.Vector2(0, 0)
        for joy in self.joysticks.values():
            try:
                rx, ry = joy.get_axis(2), joy.get_axis(3)
                if abs(rx) > 0.2: vec.x += rx
                if abs(ry) > 0.2: vec.y += ry
            except: pass
        if vec.length() > 1.0: vec = vec.normalize()
        return vec

    def is_attack_pressed(self):
        if pygame.key.get_pressed()[pygame.K_SPACE]: return True
        
        for jid, joy in self.joysticks.items():
            try:
                val = joy.get_axis(5)
                resting = self.trigger_offsets[jid]['axis5']
                
                # If resting is ~1.0, we look for values < 0.0 (Inverted)
                # If resting is ~ -1.0 or 0.0, we look for values > 0.5 (Normal)
                if resting > 0.5:
                    if val < 0.0: return True
                else:
                    if val > 0.5: return True
                
                if joy.get_button(5): return True
            except: pass
        return False

    def is_dash_pressed(self):
        if pygame.key.get_pressed()[pygame.K_LSHIFT]: return True
        
        for jid, joy in self.joysticks.items():
            try:
                if joy.get_button(0): return True # 'A' Button
                
                val = joy.get_axis(4)
                resting = self.trigger_offsets[jid]['axis4']
                
                # Same logic for Left Trigger
                if resting > 0.5:
                    if val < 0.0: return True
                else:
                    if val > 0.5: return True
            except: pass
        return False