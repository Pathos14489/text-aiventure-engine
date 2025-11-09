from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class UpperBodyUnderwear(BaseItem):
    """Underwear Schema - An underwear item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^UpperBodyUnderwear$")
    name: str = Field(description="The name of the underwear.", examples=[
        "Bra",
        "Panties",
        "Red Bikini Top",
        "Sports Bra"
    ])
    physical_description: str = Field(description="A physical description of the underwear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a bra with a floral pattern and lace trim",
        "a bikini top with a bright red color and a halter neck",
        "a sports bra with a comfortable fit and moisture-wicking fabric",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the underwear rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)

    @staticmethod
    def from_json(data: dict) -> "UpperBodyUnderwear":
        """Deserialize a JSON object into an UpperBodyUnderwear instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return UpperBodyUnderwear(**data)