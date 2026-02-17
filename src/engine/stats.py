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
        self.update_derived_stats()
        self.current_hp = self.max_hp

    def update_derived_stats(self):
        self.max_hp = self.vitality * 10
        self.damage = self.strength * 2
        self.speed = 0.5 + (self.agility * 0.05)

    def modify_hp(self, amount):
        self.current_hp += amount
        if self.current_hp > self.max_hp: self.current_hp = self.max_hp
        if self.current_hp < 0: self.current_hp = 0