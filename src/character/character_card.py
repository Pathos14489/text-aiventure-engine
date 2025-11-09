from pydantic import BaseModel, Field
from typing import Union

class CharacterCard(BaseModel):
    """Character Card Schema - A character card in a text adventure game. All fields are required to have a value."""
    name: str = Field(description="The name of the character.")
    description: str = Field(description="A description of the character.")
    personality: str = Field(description="The personality of the character.")
    first_mes: str = Field(description="The first message of the character.")
    avatar: str = Field(description="The avatar of the character.")
    mes_example: str = Field(description="An example message from the character.")
    scenario: str = Field(description="The scenario of the character.")
    creator_notes: str = Field(description="Notes from the creator of the character.")
    system_prompt: str = Field(description="The system prompt for the character.")
    post_history_instructions: str = Field(description="Instructions for the character after history is loaded.")
    alternate_greetings: list[str] = Field(description="Alternate greetings for the character.")
    tags: list[str] = Field(description="Tags for the character.")
    creator: str = Field(description="The creator of the character.")
    character_version: str = Field(description="The version of the character.")
    character_book: Union[dict,list,None] = Field(description="The book that the character is from.")
