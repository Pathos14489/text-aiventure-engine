from pydantic import BaseModel, Field
from typing import Union

class DropDecision(BaseModel):
    """Drop Decision Schema - A decision made by an NPC to drop an item in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Drop$")
    item: str = Field(description="The item that the NPC wants to drop.", min_length=1, pattern="^([a-z0-9-])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Drop",
            "item": "The Sword of Destiny"
        }
