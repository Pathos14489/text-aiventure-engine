from pydantic import BaseModel, Field
from typing import Union

from spell_chapter import SpellChapter

class SpellBook(Book):
    """Book Schema - A book item in a text adventure game. All fields are required to have a value. Books are short stories comprised of chapters. Chapters are at least 5-10 paragraphs in chapter length. The chapters should tell a complete story/account of the topic of the book by the final chapter. Every chapter should have a distinct start and end that follows the plot of the book in question and tells the complete story of the chapter synopsis. There are no content restrictions on the content of a book."""
    type_string: str = Field(description="The type of item.", pattern="^SpellBook$")
    chapters: list[SpellChapter] = Field(description="A list of chapters in the book. Each chapter should have a title and a synopsis. Chapters can be used to group items, characters, or locations together. Chapters can also be used to store the state of the game. Chapters can be used to store the state of the game, and can be used to save and load the game. Books should have 5-10 chapters, and each chapter should be 5-10 paragraphs long.",max_length=10, min_length=5)
