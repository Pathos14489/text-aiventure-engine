from pydantic import BaseModel, Field
from typing import Union
import random

from src.utils import preprocess

class MagicalAttributes(BaseModel):
    """Magical Attributes for a character, 0-10"""
    power: int = Field(ge=0, le=10) # Magical Power - Determines the strength and effectiveness of magical abilities.
    precision: int = Field(ge=0, le=10) # Magical Precision - Affects the accuracy and control of magical spells.
    fortitude: int = Field(ge=0, le=10) # Magical Fortitude - Influences resistance to magical attacks and effects.
    flourish: int = Field(ge=0, le=10) # Magical Flourish - Impacts the visual and sensory impact of magical abilities.
    willpower: int = Field(ge=0, le=10) # Magical Willpower - Affects the character's ability to resist magical effects and maintain concentration.
    multitasking: int = Field(ge=0, le=10) # Magical Multitasking - Determines how many magical effects or spells a character can maintain simultaneously.
    attunement: int = Field(ge=0, le=10) # Magical Attunement - Influences the character's connection to magical energies and their ability to sense magical phenomena.

    def __init__(self, **data):
        data = preprocess(data, base_ten_field_names=[
            "power",
            "precision",
            "fortitude",
            "flourish",
            "willpower",
            "multitasking",
            "attunement"
        ])
        super().__init__(**data)

    def to_json(self):
        """Get a list of all magical attributes and their values"""
        return {
            "power": self.power,
            "precision": self.precision,
            "fortitude": self.fortitude,
            "flourish": self.flourish,
            "willpower": self.willpower,
            "multitasking": self.multitasking,
            "attunement": self.attunement
        }
    
    @staticmethod
    def from_json(data: dict):
        return MagicalAttributes(**data)

    def power_check(self):
        roll = random.randint(1, 10)
        return roll <= self.power

    def precision_check(self):
        roll = random.randint(1, 10)
        return roll <= self.precision

    def fortitude_check(self):
        roll = random.randint(1, 10)
        return roll <= self.fortitude

    def flourish_check(self):
        roll = random.randint(1, 10)
        return roll <= self.flourish

    def willpower_check(self):
        roll = random.randint(1, 10)
        return roll <= self.willpower

    def multitasking_check(self):
        roll = random.randint(1, 10)
        return roll <= self.multitasking

    def attunement_check(self):
        roll = random.randint(1, 10)
        return roll <= self.attunement
