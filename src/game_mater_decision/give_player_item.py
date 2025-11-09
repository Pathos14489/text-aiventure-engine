from pydantic import BaseModel, Field
from typing import Union

class GivePlayerItemDecision(BaseModel):
    """Give Player Item Decision Schema - A decision made by the game master to give the player an item in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^GivePlayerItem$")
    item: str = Field(description="The item that the game master wants to give to the player.", min_length=1, pattern="^([a-z0-9- ])*$", examples=[
        "A shiny sword.",
        "A rusty dagger.",""
        "A magical staff.",
        "A healing potion.",
        "A mysterious amulet."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "GivePlayerItem",
            "item": "A shiny sword."
        }
