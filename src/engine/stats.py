# src/engine/stats.py
class AttributeManager:
    def __init__(self, base_str=5, base_agi=5, base_int=5, base_vit=5):
        self.strength = base_str
        self.agility = base_agi
        self.intelligence = base_int
        self.vitality = base_vit

        self.level = 1
        self.xp = 0
        self.xp_next = 100
        self.attribute_points = 0

        self.max_hp = 0
        self.current_hp = 0
        
        self.update_derived_stats()
        self.current_hp = self.max_hp

    def update_derived_stats(self):
        old_max_hp = self.max_hp
        self.max_hp = self.vitality * 10
        self.damage = self.strength * 2
        self.speed = 0.5 + (self.agility * 0.05)

        if old_max_hp > 0:
            diff = self.max_hp - old_max_hp
            self.current_hp += diff
            if self.current_hp < 1: self.current_hp = 1
            if self.current_hp > self.max_hp: self.current_hp = self.max_hp

    def gain_xp(self, amount):
        self.xp += amount
        print(f"XP Gained: {amount} | Total: {self.xp}/{self.xp_next}") # DEBUG PRINT
        if self.xp >= self.xp_next:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_next
        # Simplified Curve for testing: Level * 100
        self.xp_next = self.level * 100 
        self.attribute_points += 5
        
        self.update_derived_stats()
        self.current_hp = self.max_hp
        print(f"*** LEVEL UP! Level {self.level} ***")

    def modify_hp(self, amount):
        self.current_hp += amount
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp
        if self.current_hp < 0:
            self.current_hp = 0