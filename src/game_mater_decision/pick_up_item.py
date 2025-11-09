from pydantic import BaseModel, Field
from typing import Union

class PickUpItemDecision(BaseModel):
    """Pick Up Item Decision Schema - A decision made by the game master to pick up an item from a location in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^PickUp$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to pick up the item for.", min_length=1, pattern="^([a-z0-9- ])*$")
    item: str = Field(description="The name of the item that the game master wants to pick up from the location.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "PickUp",
            "target_character_name": "John Doe",
            "item": "The Sword of Destiny"
        }