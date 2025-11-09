from pydantic import BaseModel, Field
from typing import Union

class TeleportDecision(BaseModel):
    """Teleport Decision Schema - A decision made by the game master to teleport a character to a new location in the text adventure game. Teleports don't leave a path between where they were and where they went. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Teleport$")
    character: str = Field(description="The full name of the character that the game master wants to teleport.", min_length=1, pattern="^([a-z0-9- ])*$")
    location: str = Field(description="The location that the game master wants to teleport the character to.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Teleport",
            "character": "John Doe",
            "location": "The Dark Cave"
        }
