from pydantic import BaseModel, Field

from src.utils import generate_id

class Chapter(BaseModel):
    """Chapter Schema - A chapter in a book. All fields are required to have a value. Books are composed of chapters. Chapters are at least 5-25 paragraphs in chapter_paragraphs length."""
    id: str = Field(default_factory=generate_id)
    chapter_title: str = Field(...,description="The title of the chapter. Should be at least a sentence long.", min_length=1)
    chapter_synopsis: str = Field(...,description="A synopsis of the chapter. Should be at least a sentence long.", min_length=1)
    chapter_length: str = Field(...,description="The length of the chapter. Should be a short description of the chapter length.", examples=["Short: 5","Medium: 15","Long: 25"], pattern="^(Short: 5|Medium: 15|Long: 25)$")
    chapter_paragraphs: list[str] = Field(description="The full content of the chapter as a list of paragraphs. Should be at least 10-20 paragraphs long.", min_length=5, max_length=25)

    def to_json(self):
        return {
            "id": self.id,
            "chapter_title": self.chapter_title,
            "chapter_synopsis": self.chapter_synopsis,
            "chapter_length": self.chapter_length,
            "chapter_paragraphs": self.chapter_paragraphs
        }
    
    @staticmethod
    def from_json(data: dict) -> "Chapter":
        """Deserialize a JSON object into a Chapter instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Chapter(**data)