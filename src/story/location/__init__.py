from pydantic import BaseModel, Field
from typing import Union

from src.utils import generate_id
from src.character import Character
import src.items as Items

from .travelable_location import TravelableLocation, TravelableLocation_Prompt

class Location(BaseModel):
    """Location Schema - A location in a text adventure game. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that they are all separate sections that should cohesively flow together, seperated by new lines, and not repeat themselves. Tags are used to help search for locations, and can be things like "Forest", "Castle", "Desert", etc. All fields are required to have a value."""
    id: str = Field(default_factory=generate_id)
    name: str = Field(description="The name of the location.", min_length=1, examples=[
        "The Dark Cave",
        "The Enchanted Forest",
        "The Haunted Mansion",
        "The Abandoned Town",
        "The Deserted Island",
        "The Lost City"
    ])
    location_physical_description: str = Field(description="A description of the location. Should be at least a paragraph long. MUST NOT contain any information about items or characters in the location. This should strictly be a description of the location without any storytelling involved. No talking about how the player moves, don't include plot elements or thoughts that the player is thinking, merely describe the location as detailedly as possible. This should NOT describe the items or characters in the location, only the physical description of the location itself. If the user's prompt includes objects or characters in the location, they should be described in the objects_in_location and npcs_in_location fields ONLY.", min_length=1, examples=[
        "A dark, damp cave with a low ceiling and a musty smell.",
        "A dense, overgrown forest with tall trees and thick underbrush.",
        "A large, spooky mansion with creaky floors and drafty hallways.",
        "An old, abandoned town with crumbling buildings and overgrown streets.",
        "A small, sandy island with palm trees and crystal clear water.",
        "A ruined city with crumbling buildings and twisted metal."
    ])
    travel_destinations: list[TravelableLocation] = Field(description="A list of locations that can be traveled to from this location. Each travelable location should have a portal, location name, and location prompt. All possible travelable locations from this location. If this is in a section of a town for instance, it could have a travelable location to the market, the inn, the blacksmith, travelable locations out of town, travelable locations to the other parts of town, etc. Be detailed when coming up with travelable locations. Travel locations should usually be logical and reasonable. For example, if you're lost in a white void with just a cake, you could do \"Explore the void\" but wouldn't do \"The Cake\" unless the cake was large enough to stand on.", min_length=1)
    loot_prompt: str = Field(description="A description of the loot in the location. Should be at least a sentence long. This should describe the items in the location that the player can interact with, pick up, use, etc. This should NOT describe the location itself, only the items in the location. If there are no items in the location, this should say 'There are no items in this location.'", min_length=1, examples=[
        "The cave is filled with old, rusty tools and broken crates.",
        "The forest floor is littered with fallen branches and leaves, but you also spot a few shiny objects glinting in the underbrush.",
        "The mansion is filled with antique furniture and dusty old books, but you also notice a few valuable-looking items scattered about.",
        "The town is filled with abandoned buildings and overgrown streets, but you also see a few useful items lying around.",
        "The island is mostly empty, but you do find a few useful items washed up on the shore.",
        "The city is filled with rubble and debris, but you also spot a few valuable items among the ruins."
    ])
    objects_in_location: list[Items.SomeItem] = Field(description="A list of objects in the location. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required Attributes. If an item is a weapon, it MUST have a damage value and required Attributes. If an item is food, it MUST have a hunger restored and thirst restored value.")
    npcs_in_location: list[Character] = Field(description="A list of characters in the location.")

    def to_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "location_physical_description": self.location_physical_description,
            "travel_destinations": [destination.to_json() for destination in self.travel_destinations],
            "loot_prompt": self.loot_prompt
        }
    
    @staticmethod
    def from_json(data: dict):
        if isinstance(data, Location):
            return data
        data['travel_destinations'] = [TravelableLocation.from_json(dest) for dest in data.get('travel_destinations', [])]
        data['objects_in_location'] = [Items.from_json(item) for item in data.get('objects_in_location', [])]
        data['npcs_in_location'] = [Character.from_json(npc) for npc in data.get('npcs_in_location', [])]
        return Location(**data)