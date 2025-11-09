from pydantic import BaseModel, Field
from typing import Union

class FurtherDescribeCurrentLocationDecision(BaseModel):
    """Further Describe Current Location Decision Schema - A decision made by the game master to modify the physical description of the current location in the text adventure game. This should only be used to further describe more details about the current location, not the actions of the players or NPCs in the location. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^ModifyLocationDescription$")
    description_addition: str = Field(description="The description that the game master wants to add to the current location.", min_length=1, pattern="^[A-Z]([a-z0-9- ])*$", examples=[
        "As you look closer, you see a small glimmer of light in the distance.",
        "You hear a faint rustling sound coming from the bushes.",
        "A strange smell fills the air, like something rotting.",
        "You notice a small crack in the wall that wasn't there before.",
        "A shadow flits past your vision, but when you turn to look, there's nothing there."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "ModifyLocationDescription",
            "description_addition": "As you look closer, you see a small glimmer of light in the distance."
        }
