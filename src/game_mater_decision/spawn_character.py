from pydantic import BaseModel, Field
from typing import Union

class SpawnCharacterDecision(BaseModel):
    """Spawn Character Decision Schema - A decision made by the game master to spawn a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^CharacterSpawn$")
    prompt: str = Field(description="The prompt that the game master wants to use to spawn the character.", min_length=1, pattern="^([a-z0-9- ])*$", examples=[
        "A brave knight.",
        "A cunning thief.",
        "A wise wizard.",
        "A fierce warrior.",
        "A skilled archer."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "CharacterSpawn",
            "prompt": "A brave knight."
        }
