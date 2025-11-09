from pydantic import BaseModel, Field
from typing import Union

class AttackDecision(BaseModel):
    """Attack Decision Schema - A decision made by an NPC to attack another NPC in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Attack$")
    target: str = Field(description="The target that the NPC wants to attack.", min_length=1, pattern="^([a-z0-9-])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Attack",
            "target": "The Dragon"
        }
