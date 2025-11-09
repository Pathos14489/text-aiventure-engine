from pydantic import BaseModel, Field
from typing import Union

class KillDecision(BaseModel):
    """Kill Decision Schema - A decision made by the game master to kill a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Kill$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to kill.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Kill",
            "target_character_name": "John Doe"
        }
        