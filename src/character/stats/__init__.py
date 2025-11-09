from pydantic import BaseModel, Field
from typing import Union

from .attributes import Attributes
from .magical_attributes import MagicalAttributes
from .skills import Skills

from src.utils import preprocess

class Stats(BaseModel):
    """Stats for a character"""
    # Needs Stats
    hunger: int = Field(100, ge=0, le=100, description="The character's hunger level. This is used for things like how hungry the character is, how much they need to eat, etc.")
    thirst: int = Field(100, ge=0, le=100, description="The character's thirst level. This is used for things like how thirsty the character is, how much they need to drink, etc.")
    fatigue: int = Field(100, ge=0, le=100, description="The character's fatigue level. This is used for things like how tired the character is, how much they need to rest, etc.")

    # Energy Levels
    hp: int = Field(100, ge=0, description="The character's health points. This is used for things like how much damage the character can take before dying, etc.")
    max_hp: int = Field(100, ge=0, description="The character's maximum health points.")
    action_points: int = Field(100, ge=0, description="The character's action points. This is used for things like how many actions the character can take in a turn, etc. Every action and every equipable item takes AP to do.")
    max_action_points: int = Field(100, ge=0, description="The character's maximum action points.")
    mana: int = Field(100, ge=0, description="The character's mana points. This is used for things like how much magical energy the character has to cast spells, etc.")
    max_mana: int = Field(100, ge=0, description="The character's maximum mana points.")

    # Experience and Level
    experience: int = Field(0, ge=0, description="The character's experience points.")
    experience_to_next_level: int = Field(100, ge=0, description="The experience points needed to reach the next level.")
    level: int = Field(1, ge=1, description="The character's level.")

    def __init__(self, **data):
        data = preprocess(data, base_one_hundred_field_names=[
            "hunger",
            "thirst",
            "fatigue"
        ])
        super().__init__(**data)

    def to_json(self):
        """Get a dictionary of all stats and their values"""
        return {
            "hunger": self.hunger,
            "thirst": self.thirst,
            "fatigue": self.fatigue,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "action_points": self.action_points,
            "max_action_points": self.max_action_points,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "experience": self.experience,
            "experience_to_next_level": self.experience_to_next_level,
            "level": self.level
        }
    
    @staticmethod
    def from_json(data: dict):
        return Stats(**data)

    def restore(self):
        """Restore all stats to maximum"""
        self.hunger = 100
        self.thirst = 100
        self.fatigue = 100
        self.hp = self.max_hp
        self.action_points = self.max_action_points
        self.mana = self.max_mana

    def set_max_hp(self, max_hp: int):
        """Set maximum HP and adjust current HP if necessary"""
        self.max_hp = max_hp
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def set_max_action_points(self, max_action_points: int):
        """Set maximum Action Points and adjust current Action Points if necessary"""
        self.max_action_points = max_action_points
        if self.action_points > self.max_action_points:
            self.action_points = self.max_action_points

    def set_max_mana(self, max_mana: int):
        """Set maximum Mana and adjust current Mana if necessary"""
        self.max_mana = max_mana
        if self.mana > self.max_mana:
            self.mana = self.max_mana

    def modify_hunger(self, amount: int):
        """Modify Hunger by amount, cannot go below 0 or above 100"""
        self.hunger = max(0, min(self.hunger + amount, 100))
    def modify_thirst(self, amount: int):
        """Modify Thirst by amount, cannot go below 0 or above 100"""
        self.thirst = max(0, min(self.thirst + amount, 100))
    def modify_fatigue(self, amount: int):
        """Modify Fatigue by amount, cannot go below 0 or above 100"""
        self.fatigue = max(0, min(self.fatigue + amount, 100))

    def modify_hp(self, amount: int):
        """Modify HP by amount, cannot go below 0 or above max_hp"""
        self.hp = max(0, min(self.hp + amount, self.max_hp))
    def modify_action_points(self, amount: int):
        """Modify Action Points by amount, cannot go below 0 or above max_action_points"""
        self.action_points = max(0, min(self.action_points + amount, self.max_action_points))
    def modify_mana(self, amount: int):
        """Modify Mana by amount, cannot go below 0 or above max_mana"""
        self.mana = max(0, min(self.mana + amount, self.max_mana))
