from pydantic import BaseModel, Field
from typing import Union

from src.items.readable.chapter import Chapter
from src.magic.spell import Spell

class SpellChapter(Chapter):
    """Chapter Schema - A chapter in a book. All fields are required to have a value. Books are composed of chapters. Chapters are at least 5-25 paragraphs in chapter_paragraphs length."""
    chapter_title: str = Field(...,description="The title of the chapter. Should be at least a sentence long.", min_length=1)
    chapter_synopsis: str = Field(...,description="A synopsis of the chapter. Should be at least a sentence long.", min_length=1)
    spell: Spell = Field(...,description="The spell associated with this chapter.")
    chapter_length: str = Field(...,description="The length of the chapter. Should be a short description of the chapter length.", examples=["Short: 5","Medium: 15","Long: 25"], pattern="^(Short: 5|Medium: 15|Long: 25)$")
    chapter_paragraphs: list[str] = Field(description="The full content of the chapter as a list of paragraphs. Should be at least 10-20 paragraphs long.", min_length=5, max_length=25)
