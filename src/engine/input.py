# src/engine/input.py
import pygame

class InputManager:
    def __init__(self):
        self.joysticks = {}
        self.init_joysticks()
        
    def init_joysticks(self):
        """Detects and initializes all connected controllers."""
        pygame.joystick.init()
        # Clear old dictionary
        self.joysticks = {}
        
        for i in range(pygame.joystick.get_count()):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                # Use instance_id as key for robustness (if supported), else id
                jid = joy.get_instance_id() if hasattr(joy, "get_instance_id") else i
                self.joysticks[jid] = joy
                print(f"🎮 Controller Connected: {joy.get_name()}")
            except Exception as e:
                print(f"⚠️ Failed to init controller {i}: {e}")

    def handle_hotplug(self, event):
        """Call this in main loop when JOYDEVICEADDED/REMOVED events happen."""
        if event.type == pygame.JOYDEVICEADDED:
            self.init_joysticks()
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.init_joysticks()
            print("🔌 Controller Disconnected")

    def get_movement_vector(self):
        """Returns normalized vector for movement (WASD + Left Stick)."""
        vec = pygame.math.Vector2(0, 0)
        keys = pygame.key.get_pressed()

        # Keyboard
        if keys[pygame.K_w] or keys[pygame.K_UP]: vec.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: vec.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: vec.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: vec.x += 1

        # Controller (First available)
        if self.joysticks:
            try:
                # Get the first joystick object
                joy = list(self.joysticks.values())[0]
                
                # Axes 0 (Left/Right) and 1 (Up/Down) are standard Left Stick
                # We add a 'deadzone' of 0.2 to prevent drift
                x_axis = joy.get_axis(0)
                y_axis = joy.get_axis(1)
                
                if abs(x_axis) > 0.2: vec.x += x_axis
                if abs(y_axis) > 0.2: vec.y += y_axis
            except:
                pass # Ignore controller errors to prevent crash

        if vec.length() > 1.0:
            vec = vec.normalize()
            
        return vec

    def is_action_pressed(self, action="attack"):
        """Checks Spacebar or Controller Button 'A' (Button 0)."""
        keys = pygame.key.get_pressed()
        
        # Keyboard
        if keys[pygame.K_SPACE]: return True
        
        # Controller
        if self.joysticks:
            try:
                joy = list(self.joysticks.values())[0]
                # Button 0 is usually 'A' on Xbox / 'X' on PS
                if joy.get_button(0): return True
            except:
                pass
                
        return False