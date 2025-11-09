from pydantic import BaseModel, Field
from typing import Union

class ActionDecision(BaseModel):
    """Action Decision Schema - A decision made by an NPC to roleplay an arbitrary action in the text adventure game. All fields are required to have a value. Roleplaying arbitrary actions has no effect on the state of the game world, the objects in it, or the NPCs within it, and is purely for aesthetic."""
    type_string: str = Field(description="The type of decision.", pattern="^Action$")
    message: str = Field(description="The message that the NPC wants to say.", min_length=1, examples=[
        "opens the door",
        "shakes their head",
        "sighs",
        "nods",
        "smiles and gives David a hug",
    ], pattern="^[a-z]([A-Za-z0-9 ])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Action",
            "message": "opens the door"
        }
