from pydantic import BaseModel, Field
from typing import Union
import random

from src.utils import preprocess

class Skills(BaseModel):
    """Skills for a character, 0-100"""
    # Weapon Skills
    melee_weapons: int = Field(ge=0, le=100) # Close combat weapons like knives, swords, clubs, etc.
    unarmed: int = Field(ge=0, le=100) # Hand-to-hand combat skills
    firearms: int = Field(ge=0, le=100) # Guns and projectile weapons
    energy_weapons: int = Field(ge=0, le=100) # Laser, plasma, and other energy-based weapons. Also covers magical ranged weapons if applicable
    explosives: int = Field(ge=0, le=100) # Grenades, mines, and other explosive devices
    
    # Other Skills
    lockpicking: int = Field(ge=0, le=100) # Opening locked doors and containers
    hacking: int = Field(ge=0, le=100) # Bypassing electronic security systems
    speech: int = Field(ge=0, le=100) # Persuasion and negotiation
    medical: int = Field(ge=0, le=100) # Non-magical healing and first aid
    scavenging: int = Field(ge=0, le=100) # Finding useful items in the environment

    # Crafting Skills
    cooking: int = Field(ge=0, le=100) # Combine any number of food items to make a new food item
    crafting: int = Field(ge=0, le=100) # Combine any number of 2+ items to make a new item

    # Magical Skills (if applicable)
    spellcasting: int = Field(ge=0, le=100) # Using existing spells
    spellcrafting: int = Field(ge=0, le=100) # Creating new spells
    spell_memorization: int = Field(ge=0, le=100) # Skill level at which a character can memoize spells found in scrolls and spell books. Higher levels allow for memorizing higher level spells and better consistency.
    spell_deconstruction: int = Field(ge=0, le=100) # Skill level at which a character can deconstruct spells from scrolls and spell books into their base components for later use in spellcrafting. Higher levels allow for deconstructing higher level spells and better yield.

    def __init__(self, **data):
        data = preprocess(data, base_one_hundred_field_names=[
            "melee_weapons",
            "unarmed",
            "firearms",
            "energy_weapons",
            "explosives",
            "lockpicking",
            "hacking",
            "speech",
            "medical",
            "scavenging",
            "cooking",
            "crafting",
            "spellcasting",
            "spellcrafting",
            "spell_memorization",
            "spell_deconstruction"
        ])
        super().__init__(**data)

    def to_json(self):
        """Get a list of all skills and their values"""
        return {
            # Weapon Skills
            "melee_weapons": self.melee_weapons,
            "unarmed": self.unarmed,
            "firearms": self.firearms,
            "energy_weapons": self.energy_weapons,
            "explosives": self.explosives,
            # Other Skills
            "lockpicking": self.lockpicking,
            "hacking": self.hacking,
            "speech": self.speech,
            "medical": self.medical,
            "scavenging": self.scavenging,
            # Crafting Skills
            "cooking": self.cooking,
            "crafting": self.crafting,
            # Magical Skills (if applicable)
            "spellcasting": self.spellcasting,
            "spellcrafting": self.spellcrafting,
            "spell_memorization": self.spell_memorization,
            "spell_deconstruction": self.spell_deconstruction
        }

    @staticmethod
    def from_json(data: dict):
        return Skills(**data)
    
    # Weapon Skills

    def melee_weapon_check(self):
        roll = random.randint(1, 100)
        return roll <= self.melee_weapons
    
    def firearms_check(self):
        roll = random.randint(1, 100)
        return roll <= self.firearms

    def energy_weapon_check(self):
        roll = random.randint(1, 100)
        return roll <= self.energy_weapons

    def explosive_check(self):
        roll = random.randint(1, 100)
        return roll <= self.explosives

    # Other Skills

    def lockpicking_check(self):
        roll = random.randint(1, 100)
        return roll <= self.lockpicking
    
    def hacking_check(self):
        roll = random.randint(1, 100)
        return roll <= self.hacking
            
    def speech_check(self):
        roll = random.randint(1, 100)
        return roll <= self.speech
    
    def medical_check(self):
        roll = random.randint(1, 100)
        return roll <= self.medical

    def scavenging_check(self):
        roll = random.randint(1, 100)
        return roll <= self.scavenging

    # Crafting Skills

    def cooking_check(self):
        roll = random.randint(1, 100)
        return roll <= self.cooking

    def crafting_check(self):
        roll = random.randint(1, 100)
        return roll <= self.crafting

    # Magical Skills (if applicable)

    def spellcasting_check(self):
        roll = random.randint(1, 100)
        return roll <= self.spellcasting

    def spellcrafting_check(self):
        roll = random.randint(1, 100)
        return roll <= self.spellcrafting

    def spell_memorization_check(self):
        roll = random.randint(1, 100)
        return roll <= self.spell_memorization

    def spell_deconstruction_check(self):
        roll = random.randint(1, 100)
        return roll <= self.spell_deconstruction
