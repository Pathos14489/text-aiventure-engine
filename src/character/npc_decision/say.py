from pydantic import BaseModel, Field
from typing import Union

class SayDecision(BaseModel):
    """Say Decision Schema - A decision made by an NPC to say smoething in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Say$")
    message: str = Field(description="The message that the NPC wants to say.", min_length=1)

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Say",
            "message": "Hello, how are you?"
        }
