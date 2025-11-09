from pydantic import BaseModel, Field
from typing import Union

class SpawnNewLocationDecision(BaseModel):
    """Spawn New Location Decision Schema - A decision made by the game master to spawn a new location in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^NewLocationSpawn$")
    prompt: str = Field(description="The prompt that the game master wants to use to spawn the new location.", min_length=1, pattern="^([a-z0-9- ])*$", examples=[
        "A hidden cave entrance under the waterfall.",
        "A secret passage behind a bookshelf that leads to a hidden room.",
        "A hidden door to the outside.",
        "A trapdoor in the floor.",
        "A secret tunnel leading to the end of the dungeon."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "NewLocationSpawn",
            "prompt": "A hidden cave entrance under the waterfall."
        }
