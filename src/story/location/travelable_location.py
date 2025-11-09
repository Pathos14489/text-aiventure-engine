from pydantic import BaseModel, Field
from typing import Union

from src.utils import preprocess, generate_id

class TravelableLocation(BaseModel):
    """Travelable Location Schema - A location in a text adventure game that can be traveled to. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Setting, Atmosphere, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Tags are used to help search for locations, and can be things like "Forest", "Castle", "Desert", etc. All fields are required to have a value. These should be physically connected locations to the Location parent that they are a part of. Examples of travelable locations include doors, gates, paths, etc. that lead to other nearby locations. The manner in which the characters travel to a new location. Travelable locations can only be large spaces, and CANNOT be objects within the current location."""
    id: str = Field(default_factory=generate_id)
    # location_type: str = Field(description="The type of location.", pattern="^(Indoors|Outdoors)$")
    portal: str = Field(description="The name of the portal that leads to this location. Can be a door, a gate, a hole in the ground, an actual portal, etc. The manner in which the characters travel to the new location. ", examples=[
        "The Door to the Kitchen",
        "A small path into the forest",
        "A large set of double doors",
        "Door leading outside",
        "Door to the Bee and Barb",
        "The Front Door"
    ])
    location_name: str = Field(description="The name of the location. Can be a city, a forest, a mountain, a cave, etc. The name of the location.", examples=[
        "Kitchen - Your House",
        "The Forest of Shadows - East Entrance",
        "The Castle of the Mad King - Throne Room",
        "Time Square - New York City",
        "The Bee and Barb",
        "City Square - Whiterun"
    ])
    location_physical_description: str = Field(description="A brief description of the location. Can be a city, a forest, a mountain, a cave, etc. The description of the location.", examples=[
        "A small kitchen in your house",
        "A dark and foreboding forest",
        "A grand throne room in a castle",
        "A bustling city square",
        "A cozy inn",
        "A large bustling city square in the middle of the day"
    ])
    movement_description: str = Field(description="A description of how the characters move to the new location. Can be via a door, a gate, a path, etc. The manner in which the characters travel to the new location.", examples=[
        "You walk through the door",
        "You step through the portal",
        "You walk down the path",
        "You walk through the gate",
        "You step through the archway",
        "You walk through the tunnel"
    ])

    def __init__(self, **data):
        data = preprocess(data)
        super().__init__(**data)

    def to_json(self):
        return {
            "portal": self.portal,
            "location_name": self.location_name,
            "location_physical_description": self.location_physical_description,
            "movement_description": self.movement_description
        }
    
    @staticmethod
    def from_json(data: dict):
        return TravelableLocation(**data)

class TravelableLocation_Prompt(BaseModel):
    """Travelable Location Prompt Schema - A prompt for a travelable location in a text adventure game. All fields are required to have a value."""
    prompt_type: str = Field(description="The type of prompt.", pattern="^TravelableLocation$")
    prompt: str = Field(description="The prompt for the travelable location.", min_length=1, examples=[
        "A hidden cave entrance under the waterfall.",
        "A secret passage behind a bookshelf that leads to a hidden room.",
        "A hidden door to the outside.",
        "A trapdoor in the floor.",
        "A secret tunnel leading to the end of the dungeon."
    ], pattern="^[A-Za-z0-9 ]*$")
