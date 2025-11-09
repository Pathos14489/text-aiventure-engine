from pydantic import BaseModel, Field
from typing import Union

class EquipItemDecision(BaseModel):
    """Equip Item Decision Schema - A decision made by the game master to equip an item to a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Equip$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to equip the item to.", min_length=1, pattern="^([a-z0-9- ])*$")
    item: str = Field(description="The name of the item that the game master wants to equip to the character.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Equip",
            "target_character_name": "John Doe",
            "item": "The Sword of Destiny"
        }
