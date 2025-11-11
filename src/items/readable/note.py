from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.items.readable.chapter import Chapter
from src.utils import generate_id

class Note(BaseItem):
    """Note Schema - A note item in a text adventure game. All fields are required to have a value. Notes are short pieces of text that can be used to convey information or clues to the player."""
    type_string: str = Field(description="The type of item.", pattern="^Note$")
    name: str
    physical_description: str = Field(description="A physical description of the note that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a small piece of paper with handwriting on it",
        "a torn page from a notebook with scribbles",
        "a folded note with a wax seal",
        "a crumpled piece of paper with a message",
        "a sticky note with a reminder",
        "a handwritten letter with a wax seal"
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the bookshelf",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    note_synopsis: str = Field(...,description="A synopsis of the note. Should be at least a sentence long.", min_length=1)
    note_title: str = Field(...,description="The title of the note.", examples=["A Mysterious Message","The Secret Plan","Notes from the Past"], pattern="^[A-Za-z0-9 ]+$")
    note_length: str = Field(...,description="The length of the note. Should be a short description of the note length.", examples=["Short: 5","Medium: 15","Long: 25"], pattern="^(Short: 5|Medium: 15|Long: 25)$")
    note_paragraphs: list[str] = Field(description="The full content of the note as a list of paragraphs. Should be at least 10-20 paragraphs long.", min_length=5, max_length=25)

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "note_synopsis": self.note_synopsis,
            "note_title": self.note_title,
            "note_length": self.note_length,
            "note_paragraphs": self.note_paragraphs
        })
        return json_out

    @staticmethod
    def from_json(data: dict) -> "Note":
        """Deserialize a JSON object into a Note instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Note(**data)