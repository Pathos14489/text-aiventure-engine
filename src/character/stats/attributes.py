from pydantic import BaseModel, Field
from typing import Union
import random

from src.utils import preprocess

class Attributes(BaseModel):
    """Attributes for a character, 1-10"""
    strength: int = Field(ge=0, le=10)
    perception: int = Field(ge=0, le=10)
    endurance: int = Field(ge=0, le=10)
    charisma: int = Field(ge=0, le=10)
    intelligence: int = Field(ge=0, le=10)
    agility: int = Field(ge=0, le=10)
    luck: int = Field(ge=0, le=10)

    def __init__(self, **data):
        data = preprocess(data, base_ten_field_names=[
            "strength",
            "perception",
            "endurance",
            "charisma",
            "intelligence",
            "agility",
            "luck"
        ])
        super().__init__(**data)

    def to_json(self):
        """Get a list of all attributes and their values"""
        return {
            "strength": self.strength,
            "perception": self.perception,
            "endurance": self.endurance,
            "charisma": self.charisma,
            "intelligence": self.intelligence,
            "agility": self.agility,
            "luck": self.luck
        }
    
    @staticmethod
    def from_json(data: dict):
        return Attributes(**data)

    def strength_check(self):
        roll = random.randint(1, 10)
        return roll <= self.strength

    def perception_check(self):
        roll = random.randint(1, 10)
        return roll <= self.perception

    def endurance_check(self):
        roll = random.randint(1, 10)
        return roll <= self.endurance

    def charisma_check(self):
        roll = random.randint(1, 10)
        return roll <= self.charisma

    def intelligence_check(self):
        roll = random.randint(1, 10)
        return roll <= self.intelligence

    def agility_check(self):
        roll = random.randint(1, 10)
        return roll <= self.agility

    def luck_check(self):
        roll = random.randint(1, 10)
        return roll <= self.luck
