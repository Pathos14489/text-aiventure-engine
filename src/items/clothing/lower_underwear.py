from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class LowerUnderwear(BaseItem):
    """Lower Underwear Schema - An underwear item in a text adventure game. All fields are required to have a value. Underwear can also be a swimsuit, or other undergarments."""
    type_string: str = Field(description="The type of item.", pattern="^LowerUnderwear$")
    name: str = Field(description="The name of the underwear.", examples=[
        "Boxers",
        "Briefs",
        "Red Bikini Bottom",
        "Thong"
    ])
    physical_description: str = Field(description="A physical description of the underwear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a pair of black lace panties with a floral pattern",
        "a red bikini bottom with a high-cut leg and a comfortable fit",
        "a pair of blue boxer shorts with a fun print and an elastic waistband",
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
    def from_json(data: dict) -> "LowerUnderwear":
        """Deserialize a JSON object into a LowerUnderwear instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return LowerUnderwear(**data)