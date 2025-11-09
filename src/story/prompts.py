from pydantic import BaseModel, Field
from typing import Union

from src.character import Character_Prompt
from src.story.location import TravelableLocation_Prompt
from src.items import Item_Prompt

class Prompts(BaseModel):
    """Prompts Schema - A list of prompts for a text adventure game. All fields are required to have a value. The prompts should be a list of 'Character', 'Item', and 'TravelableLocation' prompts. The prompts will be used to generate the characters, items, and travelable locations in the text adventure game. All fields are required to have a value."""
    prompts: list[Union[Character_Prompt,Item_Prompt,TravelableLocation_Prompt]] = Field(description="A list of prompts for the text adventure game. Each prompt should have a type and a prompt. All prompts for the text adventure game.", min_length=1)
    