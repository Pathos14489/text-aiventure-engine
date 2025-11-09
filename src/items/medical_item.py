from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class MedicalItem(BaseItem):
    """Medical Item Schema - A medical item in a text adventure game. All fields are required to have a value. Only Medical Items should have a health restored value."""
    type_string: str = Field(description="The type of item.", pattern="^MedicalItem$")
    name: str
    physical_description: str = Field(description="A physical description of the medical item that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a vial with a red cross symbol on it",
        "a bandage with a blue stripe",
        "a bottle of pills with a white label",
        "a syringe with a clear liquid inside",
        "a first aid kit with a green cross symbol",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "In the medicine cabinet",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    health_restored: int = Field(...,ge=0)

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "health_restored": self.health_restored
        })
        return json_out

    @staticmethod
    def from_json(data: dict) -> "MedicalItem":
        """Deserialize a JSON object into a MedicalItem instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return MedicalItem(**data)