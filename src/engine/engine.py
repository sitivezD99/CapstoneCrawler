# engine.py
import pygame
import random
from pygame.math import Vector2

def move_and_slide(rect, velocity, walls):
    rect.x += velocity.x
    for wall in walls:
        if rect.colliderect(wall):
            if velocity.x > 0: rect.right = wall.left
            if velocity.x < 0: rect.left = wall.right

    rect.y += velocity.y
    for wall in walls:
        if rect.colliderect(wall):
            if velocity.y > 0: rect.bottom = wall.top
            if velocity.y < 0: rect.top = wall.bottom
    return rect

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.trauma = 0.0
        self.max_shake_offset = 12
        self.trauma_decay_rate = 1.5

    def add_trauma(self, amount):
        self.trauma = min(self.trauma + amount, 1.0)

    def apply(self, entity_or_rect):
        if hasattr(entity_or_rect, 'rect'):
            return entity_or_rect.rect.move(self.camera.topleft)
        return entity_or_rect.move(self.camera.topleft)

    def update(self, target, dt):
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)
        
        if self.trauma > 0:
            self.trauma = max(self.trauma - self.trauma_decay_rate * dt, 0.0)
            shake_amount = (self.trauma ** 2) * self.max_shake_offset
            x += random.uniform(-1, 1) * shake_amount
            y += random.uniform(-1, 1) * shake_amount
            
        self.camera = pygame.Rect(int(x), int(y), self.width, self.height)

class InputManager:
    def __init__(self):
        pygame.joystick.init()
        self.joysticks = {}
        self.trigger_offsets = {} 
        self._scan_controllers()

    def _scan_controllers(self):
        """Initializes controllers present on boot."""
        for i in range(pygame.joystick.get_count()):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                jid = joy.get_instance_id()
                if jid not in self.joysticks:
                    self.joysticks[jid] = joy
                    self.trigger_offsets[jid] = {
                        'axis4': joy.get_axis(4) if joy.get_numaxes() > 4 else 0.0,
                        'axis5': joy.get_axis(5) if joy.get_numaxes() > 5 else 0.0
                    }
                    print(f"[INPUT] Hardware Detected: {joy.get_name()} (ID: {jid})")
            except: pass

    def handle_hotplug(self, event):
        """AAA Pygame 2.0 Hotplug - Fixes the Ghost Controller bug."""
        if event.type == pygame.JOYDEVICEADDED:
            try:
                joy = pygame.joystick.Joystick(event.device_index)
                joy.init()
                jid = joy.get_instance_id()
                self.joysticks[jid] = joy
                self.trigger_offsets[jid] = {
                    'axis4': joy.get_axis(4) if joy.get_numaxes() > 4 else 0.0,
                    'axis5': joy.get_axis(5) if joy.get_numaxes() > 5 else 0.0
                }
            except Exception as e:
                print(f"[INPUT ERROR] Could not add controller: {e}")
                
        elif event.type == pygame.JOYDEVICEREMOVED:
            jid = event.instance_id
            if jid in self.joysticks:
                try: self.joysticks[jid].quit()
                except: pass
                self.joysticks.pop(jid, None)
                self.trigger_offsets.pop(jid, None)

    def is_menu_pressed(self):
        """DIRECT POLLING: Strictly mapped to Keyboard 'M'/TAB and Controller Button 7 (Start)."""
        if pygame.key.get_pressed()[pygame.K_m] or pygame.key.get_pressed()[pygame.K_TAB]:
            return True
        for joy in self.joysticks.values():
            try:
                if joy.get_numbuttons() > 7 and joy.get_button(7): return True
            except: pass
        return False

    def is_inventory_pressed(self, event):
        """EVENT LISTENER: Strictly mapped to Keyboard 'I' and Controller Button 6 (Select)."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_i: return True
        if event.type == pygame.JOYBUTTONDOWN and event.button == 6: return True
        return False

    def get_movement_vector(self):
        vec = Vector2(0, 0)
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
        vec = Vector2(0, 0)
        for joy in self.joysticks.values():
            try:
                if joy.get_numaxes() > 3:
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
                if joy.get_numbuttons() > 5 and joy.get_button(5): return True 
                if joy.get_numaxes() > 5:
                    val = joy.get_axis(5)
                    resting = self.trigger_offsets.get(jid, {}).get('axis5', 0.0)
                    if (resting > 0.5 and val < 0.0) or (resting <= 0.5 and val > 0.5):
                        return True
            except: pass
        return False

    def is_dash_pressed(self):
        if pygame.key.get_pressed()[pygame.K_LSHIFT]: return True
        for jid, joy in self.joysticks.items():
            try:
                if joy.get_numbuttons() > 0 and joy.get_button(0): return True 
                if joy.get_numaxes() > 4:
                    val = joy.get_axis(4)
                    resting = self.trigger_offsets.get(jid, {}).get('axis4', 0.0)
                    if (resting > 0.5 and val < 0.0) or (resting <= 0.5 and val > 0.5):
                        return True
            except: pass
        return False

    def is_skill_1_pressed(self):
        if pygame.key.get_pressed()[pygame.K_x]: return True
        for joy in self.joysticks.values():
            try:
                if joy.get_numbuttons() > 2 and joy.get_button(2): return True 
            except: pass
        return False

    def is_skill_2_pressed(self):
        if pygame.key.get_pressed()[pygame.K_y]: return True
        for joy in self.joysticks.values():
            try:
                if joy.get_numbuttons() > 3 and joy.get_button(3): return True 
            except: pass
        return False

    def is_skill_3_pressed(self):
        if pygame.key.get_pressed()[pygame.K_b]: return True
        for joy in self.joysticks.values():
            try:
                if joy.get_numbuttons() > 1 and joy.get_button(1): return True 
            except: pass
        return False

class Entity:
    def __init__(self, x, y, w=32, h=32, color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.velocity = Vector2(0, 0)
        self.is_alive = True

    def draw(self, screen, camera):
        pygame.draw.rect(screen, self.color, camera.apply(self.rect))