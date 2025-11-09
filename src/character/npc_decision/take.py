from pydantic import BaseModel, Field
from typing import Union

class TakeDecision(BaseModel):
    """Take Decision Schema - A decision made by an NPC to pick up an item in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Take$")
    item: str = Field(description="The item that the NPC wants to pick up.", min_length=1, pattern="^([a-z0-9-])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Take",
            "item": "The Sword of Destiny"
        }
