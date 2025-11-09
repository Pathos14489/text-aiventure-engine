from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class LowerBodywear(BaseItem):
    """LowerBodywear Schema - A lowerbodywear item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^LowerBodywear$")
    name: str
    physical_description: str = Field(description="A physical description of the lowerbodywear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a pair of blue jeans with a faded finish and a relaxed fit",
        "a black skirt with a pleated design and a comfortable waistband",
        "a pair of green cargo pants with multiple pockets and a loose fit",
        "a red dress with a fitted bodice and a flared skirt",
        "a pair of brown shorts with a stretchy waistband and a casual style",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the pants rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    covers_legs: bool = Field(description="Whether the lowerbodywear covers the legs or not. Should be a boolean value.", examples=[True,False])
    covers_genitals: bool = Field(description="Whether the lowerbodywear covers the genitals or not. Should be a boolean value.", examples=[True,False])
    covers_butt: bool = Field(description="Whether the lowerbodywear covers the butt or not. Should be a boolean value.", examples=[True,False])

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "covers_legs": self.covers_legs,
            "covers_genitals": self.covers_genitals,
            "covers_butt": self.covers_butt
        })
        return json_out
    
    @staticmethod
    def from_json(data: dict) -> "LowerBodywear":
        """Deserialize a JSON object into a LowerBodywear instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return LowerBodywear(**data)