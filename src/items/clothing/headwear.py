from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class Headwear(BaseItem):
    """Headwear Schema - A headwear item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Headwear$")
    name: str
    physical_description: str = Field(description="A physical description of the headwear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "an elegant, shiny, golden crown with intricate designs and a large ruby in the center",
        "a simple, black baseball cap with a white logo on the front",
        "a warm, knitted beanie with a pom-pom on top and a colorful pattern",
        "a stylish fedora with a wide brim and a black band around the base",
        "a wide-brimmed sun hat with a floral pattern and a ribbon tied around the base",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the hat rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    covers_hair: bool = Field(description="Whether the headwear covers the hair or not. Should be a boolean value.", examples=[True,False])
    covers_face: bool = Field(description="Whether the headwear covers the face or not. Should be a boolean value.", examples=[True,False])

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "covers_hair": self.covers_hair,
            "covers_face": self.covers_face
        })
        return json_out

    @staticmethod
    def from_json(data: dict) -> "Headwear":
        """Deserialize a JSON object into a Headwear instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Headwear(**data)