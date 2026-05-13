# assets.py
import pygame
import os

class PlayerAnimator:
    def __init__(self):
        # 1. Load Images (Run, Idle, and Transition)
        self.run_f_sheet = self._load_image_or_failsafe("front_left.png", (255, 50, 50))
        self.run_b_sheet = self._load_image_or_failsafe("back_left.png", (200, 0, 0))
        self.idle_f_sheet = self._load_image_or_failsafe("idle_front.png", (50, 255, 50))
        self.idle_b_sheet = self._load_image_or_failsafe("idle_back.png", (0, 200, 0))
        
        # --- NEW: Transition Sheets ---
        self.trans_f_sheet = self._load_image_or_failsafe("trans_front.png", (255, 150, 50))
        self.trans_b_sheet = self._load_image_or_failsafe("trans_back.png", (200, 100, 0))

        # 2. Extract Frames
        run_f_frames = self._extract_3x3_grid(self.run_f_sheet)
        run_b_frames = self._extract_3x3_grid(self.run_b_sheet)
        idle_f_frames = self._extract_3x3_grid(self.idle_f_sheet)
        idle_b_frames = self._extract_3x3_grid(self.idle_b_sheet)
        
        # --- NEW: Extract 2x2 Transition Frames ---
        trans_f_frames = self._extract_2x2_grid(self.trans_f_sheet)
        trans_b_frames = self._extract_2x2_grid(self.trans_b_sheet)

        # 3. Auto-Flip for Right Side
        run_f_right = [pygame.transform.flip(f, True, False) for f in run_f_frames]
        run_b_right = [pygame.transform.flip(f, True, False) for f in run_b_frames]
        idle_f_right = [pygame.transform.flip(f, True, False) for f in idle_f_frames]
        idle_b_right = [pygame.transform.flip(f, True, False) for f in idle_b_frames]
        
        trans_f_right = [pygame.transform.flip(f, True, False) for f in trans_f_frames]
        trans_b_right = [pygame.transform.flip(f, True, False) for f in trans_b_frames]

        # 4. Map Dictionaries
        self.run_animations = {
            "DOWN_LEFT":  run_f_frames,   "UP_LEFT":    run_b_frames,
            "DOWN_RIGHT": run_f_right,    "UP_RIGHT":   run_b_right
        }

        self.idle_animations = {
            "DOWN_LEFT":  idle_f_frames,  "UP_LEFT":    idle_b_frames,
            "DOWN_RIGHT": idle_f_right,   "UP_RIGHT":   idle_b_right
        }
        
        self.trans_animations = {
            "DOWN_LEFT":  trans_f_frames, "UP_LEFT":    trans_b_frames,
            "DOWN_RIGHT": trans_f_right,  "UP_RIGHT":   trans_b_right
        }
        
        # 5. Independent Axis Memory
        self.facing_y = "DOWN"
        self.facing_x = "LEFT"
        self.current_dir = "DOWN_LEFT"
        
        # 6. State Machine variables
        self.state = "IDLE" # States: RUN, TRANSITION, IDLE
        self.frame_index = 0
        self.anim_timer = 0.0
        
        # 7. Speeds (Adjust trans_fps to make the slowdown feel heavier or snappier)
        self.run_fps = 16 
        self.idle_fps = 7 
        self.trans_fps = 12 

    def _load_image_or_failsafe(self, filename, fallback_color):
        # We add "assets/" to the front so it finds the files in your folder
        path = os.path.join("assets", filename) 
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
        else:
            print(f"[ASSETS ERROR] Missing '{path}'.")
            surf = pygame.Surface((96, 96), pygame.SRCALPHA)
            surf.fill(fallback_color)
            return surf

    def _extract_3x3_grid(self, sheet):
        frames = []
        frame_w = sheet.get_width() // 3
        frame_h = sheet.get_height() // 3
        for row in range(3):
            for col in range(3):
                rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
                frames.append(sheet.subsurface(rect))
        return frames

    def _extract_2x2_grid(self, sheet):
        """Reads a 2x2 image left-to-right, top-to-bottom and returns 4 frames"""
        frames = []
        frame_w = sheet.get_width() // 2
        frame_h = sheet.get_height() // 2
        for row in range(2):
            for col in range(2):
                rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
                frames.append(sheet.subsurface(rect))
        return frames

    def update(self, dt, vx, vy, is_attacking=False):
        # 1. Update Facing Memory
        if vx < -0.1: self.facing_x = "LEFT"
        elif vx > 0.1: self.facing_x = "RIGHT"
        
        if vy < -0.1: self.facing_y = "UP"
        elif vy > 0.1: self.facing_y = "DOWN"

        self.current_dir = f"{self.facing_y}_{self.facing_x}"

        # 2. State Machine Logic (Attack takes Priority!)
        is_moving_now = abs(vx) > 0.1 or abs(vy) > 0.1

        if is_attacking:
            # Force the state to ATTACK, even if standing still
            if self.state != "ATTACK":
                self.state = "ATTACK"
                self.frame_index = 0
                self.anim_timer = 0.0
        elif is_moving_now:
            if self.state != "RUN":
                self.state = "RUN"
                self.frame_index = 0
                self.anim_timer = 0.0
        else:
            # Only drop to TRANSITION if we just finished running or attacking
            if self.state == "RUN" or self.state == "ATTACK":
                self.state = "TRANSITION"
                self.frame_index = 0
                self.anim_timer = 0.0

        # 3. Handle Frame Advancement & Speeds
        if self.state in ["RUN", "ATTACK"]:
            current_fps = self.run_fps
            max_frames = 9
        elif self.state == "TRANSITION":
            current_fps = self.trans_fps
            max_frames = 4
        else: # IDLE
            current_fps = self.idle_fps
            max_frames = 9

        self.anim_timer += dt
        
        if self.anim_timer >= 1.0 / current_fps:
            self.anim_timer -= 1.0 / current_fps
            
            # Transition to IDLE when the transition animation finishes
            if self.state == "TRANSITION" and self.frame_index == max_frames - 1:
                self.state = "IDLE"
                self.frame_index = 0
            else:
                self.frame_index = (self.frame_index + 1) % max_frames

    def get_current_image(self):
        # We MUST include "SKILL_3" here so the player stays visible during the spin!
        if self.state in ["RUN", "SKILL_3", "DASHING", "ATTACK", "ATTACKING"]:
            return self.run_animations[self.current_dir][self.frame_index]
        elif self.state == "TRANSITION":
            return self.trans_animations[self.current_dir][self.frame_index]
        else:
            return self.idle_animations[self.current_dir][self.frame_index]