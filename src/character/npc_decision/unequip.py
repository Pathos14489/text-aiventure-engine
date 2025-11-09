from pydantic import BaseModel, Field
from typing import Union

class UnequipDecision(BaseModel):
    """Unequip Decision Schema - A decision made by an NPC to unequip an item in the text adventure game. This must be used to remove all clothes and to unequip weapons. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Unequip$")
    item: str = Field(description="The item that the NPC wants to unequip. This should be a simple noun from the name of the item.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Unequip",
            "item": "The Sword of Destiny"
        }
