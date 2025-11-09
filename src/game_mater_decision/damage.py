from pydantic import BaseModel, Field
from typing import Union

class DamageDecision(BaseModel):
    """Damage Decision Schema - A decision made by the game master to damage a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Damage$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to damage.", min_length=1, pattern="^([a-z0-9- ])*$")
    damage: int = Field(description="The amount of damage that the game master wants to deal to the character.", ge=1)

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Damage",
            "target_character_name": "John Doe",
            "damage": 10
        }
