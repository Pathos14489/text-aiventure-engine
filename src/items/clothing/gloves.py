from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class Gloves(BaseItem):
    """Gloves Schema - A gloves item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Gloves$")
    name: str
    physical_description: str = Field(description="A physical description of the gloves that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a pair of black leather gloves with a soft lining and a snug fit",
        "a pair of red knitted gloves with a warm and cozy feel",
        "a pair of blue rubber gloves with a textured grip and a long cuff",
        "a pair of green gardening gloves with a breathable fabric and reinforced fingertips",
        "a pair of white cotton gloves with a delicate lace trim and a comfortable fit",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the glove rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)

    @staticmethod
    def from_json(data: dict) -> "Gloves":
        """Deserialize a JSON object into a Gloves instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Gloves(**data)