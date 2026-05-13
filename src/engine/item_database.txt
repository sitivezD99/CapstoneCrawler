# item_database.py
import os
import csv
from settings import *

class GameItem:
    def __init__(self, item_id, name, category, rarity, icon, equip_slot=None):
        self.item_id = item_id
        self.name = name
        self.category = category 
        self.rarity = rarity
        self.icon = icon
        self.equip_slot = equip_slot 
        
        self.effect_stat = "N/A"
        self.effect_value = "N/A"
        self.max_stack = 99
        self.is_consumable = "False"
        self.damage_type = "N/A"
        
        # THE FIX: Explicitly setting it to prevent Ghost Variable crashes
        self.is_equipped = False
        
    @property
    def color(self):
        if self.rarity == "Rare": return COLOR_RARE
        if self.rarity == "Epic": return COLOR_EPIC
        if self.rarity == "Mythic": return COLOR_MYTHIC
        if self.rarity == "Legendary": return COLOR_LEGENDARY
        return COLOR_COMMON

    def get_csv_row(self):
        return [
            self.item_id, self.name, self.category, self.rarity,
            self.effect_stat, str(self.effect_value), str(self.max_stack),
            self.is_consumable, self.damage_type, self.icon, str(self.equip_slot)
        ]

class GlyphItem(GameItem):
    def __init__(self, item_id, name, rarity, effect_stat, effect_value, icon):
        super().__init__(item_id, name, "Glyph", rarity, icon)
        self.effect_stat = effect_stat   
        self.effect_value = effect_value 
        self.is_equipped = False # Redundant safety net

class EquipmentItem(GameItem):
    def __init__(self, item_id, name, category, rarity, equip_slot, stat, value, icon):
        super().__init__(item_id, name, category, rarity, icon, equip_slot)
        self.effect_stat = stat
        self.effect_value = value
        self.is_equipped = False # Redundant safety net

class PotionItem(GameItem):
    def __init__(self, item_id, name, rarity, heal_amount, icon):
        super().__init__(item_id, name, "Potion", rarity, icon)
        self.effect_stat = "Health"
        self.effect_value = heal_amount
        self.is_consumable = "True"

class MaterialItem(GameItem):
    def __init__(self, item_id, name, rarity, description, icon, max_stack=100):
        super().__init__(item_id, name, "Material", rarity, icon)
        self.effect_stat = "Crafting"
        self.effect_value = description
        self.max_stack = max_stack 

class ItemRegistry:
    HEADERS = ['ID', 'Name', 'Category', 'Rarity', 'Effect_Stat', 'Effect_Value', 'Max_Stack', 'Is_Consumable', 'Damage_Type', 'Icon', 'Equip_Slot']
    
    def __init__(self):
        self.items = {}
        self._initialize_game_content()
        self._sync_with_csv()

    def _initialize_game_content(self):
        raw_items = [
            GlyphItem("gl_force_1", "Force", "Rare", "Force", 0.05, "🗡️"),
            GlyphItem("gl_force_2", "Force", "Epic", "Force", 0.10, "🗡️"),
            GlyphItem("gl_force_3", "Force", "Mythic", "Force", 0.15, "🗡️"),
            GlyphItem("gl_force_4", "Force", "Legendary", "Force", 0.20, "🗡️"),
            GlyphItem("gl_reach_1", "Reach", "Rare", "Reach", 0.08, "➕"),
            GlyphItem("gl_reach_2", "Reach", "Epic", "Reach", 0.15, "➕"),
            GlyphItem("gl_reach_3", "Reach", "Mythic", "Reach", 0.22, "➕"),
            GlyphItem("gl_reach_4", "Reach", "Legendary", "Reach", 0.30, "➕"),
            GlyphItem("gl_impact_1", "Impact", "Rare", "Impact", 0.10, "💥"),
            GlyphItem("gl_impact_2", "Impact", "Epic", "Impact", 0.15, "💥"),
            GlyphItem("gl_impact_3", "Impact", "Mythic", "Impact", 0.22, "💥"),
            GlyphItem("gl_impact_4", "Impact", "Legendary", "Impact", 0.30, "💥"),
            GlyphItem("gl_haste_1", "Haste", "Rare", "Haste", 0.05, "💨"),
            GlyphItem("gl_haste_2", "Haste", "Epic", "Haste", 0.10, "💨"),
            GlyphItem("gl_haste_3", "Haste", "Mythic", "Haste", 0.15, "💨"),
            GlyphItem("gl_haste_4", "Haste", "Legendary", "Haste", 0.20, "💨"),
            GlyphItem("gl_vamp_3", "Vampire", "Mythic", "Vampire", 0.05, "❤️"),
            GlyphItem("gl_vamp_4", "Vampire", "Legendary", "Vampire", 0.07, "❤️"),
            MaterialItem("mat_stone", "Stone", "Common", "Basic material", "🪨"),
            MaterialItem("mat_magic_crystal", "Magic Crystal", "Epic", "Unlocks Stars", "💎", max_stack=999),
            PotionItem("pot_hp_1", "Minor Life Potion", "Common", 50.0, "🧪"),
            PotionItem("pot_hp_2", "Life Potion", "Rare", 150.0, "🧪"),
            PotionItem("pot_hp_3", "Greater Life Potion", "Epic", 300.0, "🧪"),
            PotionItem("pot_hp_4", "Perfect Life Potion", "Mythic", 1000.0, "🧪")
        ]
        for item in raw_items: self.items[item.item_id] = item
        
        rarities = ["Common", "Rare", "Epic", "Mythic", "Legendary"]
        mults = [1, 2, 4, 8, 15] 
        
        templates = [
            ("Sword", "Weapon", "MainHand", "Base_Damage", 10, "🗡️"),
            ("Shield", "Armor", "OffHand", "Defense", 10, "🛡️"),
            ("Chestplate", "Armor", "Chest", "Defense", 15, "👕"),
            ("Leggings", "Armor", "Legs", "Defense", 8, "👖"),
            ("Boots", "Armor", "Feet", "Defense", 5, "🥾"),
            ("Ring", "Accessory", "Ring", "Strength", 2, "💍"),
            ("Amulet", "Accessory", "Necklace", "Vigor", 2, "📿")
        ]
        
        prefixes = ["Iron", "Steel", "Mithril", "Void", "Celestial"]
        
        for i, rarity in enumerate(rarities):
            for t_name, t_cat, t_slot, t_stat, t_base_val, t_icon in templates:
                final_name = f"{prefixes[i]} {t_name}"
                item_id = f"eq_{t_name.lower()}_{i}"
                final_val = t_base_val * mults[i]
                eq_item = EquipmentItem(item_id, final_name, t_cat, rarity, t_slot, t_stat, final_val, t_icon)
                self.items[item_id] = eq_item

    def _sync_with_csv(self):
        if not os.path.exists(DB_CSV_PATH):
            self._write_full_csv()
            return
        self._write_full_csv() 

    def _write_full_csv(self):
        with open(DB_CSV_PATH, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for item in self.items.values():
                writer.writerow(item.get_csv_row())

    def get_all_items_list(self):
        return list(self.items.values())
        
    def get_enemy_loot_pool(self):
        return [item for item in self.items.values() if item.category not in ["Glyph", "Material"]]

    def get_all_glyphs(self):
        return [item for item in self.items.values() if item.category == "Glyph"]

GLOBAL_DB = ItemRegistry()