from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.items.readable.chapter import Chapter
from src.utils import generate_id

class Book(BaseItem):
    """Book Schema - A book item in a text adventure game. All fields are required to have a value. Books are short stories comprised of chapters. Chapters are at least 5-10 paragraphs in chapter length. The chapters should tell a complete story/account of the topic of the book by the final chapter. Every chapter should have a distinct start and end that follows the plot of the book in question and tells the complete story of the chapter synopsis. There are no content restrictions on the content of a book."""
    type_string: str = Field(description="The type of item.", pattern="^Book$")
    name: str
    physical_description: str = Field(description="A physical description of the book that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a dark blue book with a golden spine and a red cover",
        "a thick book with a black cover and a white spine",
        "a small book with a green cover and a yellow spine",
        "a paperback book with a blue cover and a red spine",
        "a hardcover book with a black cover and a white spine",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the bookshelf",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    # page_count: int = Field(...,ge=0)
    genre: str = Field(...,description="The genre of the book.")
    book_synopsis: str = Field(...,description="A synopsis of the book. Should be at least a sentence long.", min_length=1)
    chapters: list[Chapter] = Field(description="A list of chapters in the book. Each chapter should have a title and a synopsis. Chapters can be used to group items, characters, or locations together. Chapters can also be used to store the state of the game. Chapters can be used to store the state of the game, and can be used to save and load the game. Books should have 5-10 chapters, and each chapter should be 5-10 paragraphs long.",max_length=10, min_length=5)

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "genre": self.genre,
            "book_synopsis": self.book_synopsis,
            "chapters": [chapter.to_json() for chapter in self.chapters]
        })
        return json_out
    
    @staticmethod
    def from_json(data: dict) -> "Book":
        """Deserialize a JSON object into a Book instance."""
        chapers = data.get("chapters", [])
        del data["chapters"]
        if "id" not in data:
            data["id"] = generate_id()
        book = Book(**data)
        book.chapters = [Chapter.from_json(chapter_data) for chapter_data in chapers]
        return book