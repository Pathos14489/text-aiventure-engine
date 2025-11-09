from pydantic import BaseModel, Field

from src.utils import generate_id

from .location import Location
from .prompts import Prompts

class Story(BaseModel):
    """Story Schema - A story in a text adventure game. Summarizes the vibe and aesthetic of the story. All fields are required to have a value. Player character should not be included in starting_location's NPCs."""
    # title: str
    # setting: str = Field(description="The setting of the story. Can be a city, a forest, a mountain, a cave, etc.")
    id: str = Field(default_factory=generate_id)
    vibe: str = Field(description="The vibe of the story.")
    aesthetic: str = Field(description="The aesthetic of the story. Can be a genre, a theme, a style, etc. The overall feel of the story and the writing of the items, characters, and locations.")
    starting_location: Location = Field(description="The starting location of the story.")
    locations: list[Location] = Field(description="All locations in the story.", default_factory=list)

    def to_json(self):
        return {
            "id": self.id,
            "vibe": self.vibe,
            "aesthetic": self.aesthetic,
            "starting_location": self.starting_location.id,
        }
    
    @staticmethod
    def from_json(data: dict):
        data['locations'] = [Location.from_json(loc) for loc in data.get('locations', [])]
        for _, loc in enumerate(data['locations']):
            if loc.id == data['starting_location']:
                data['starting_location'] = loc
                break
        if isinstance(data.get('starting_location'), str):
            data['starting_location'] = None
        return Story(**data)