from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class Footwear(BaseItem):
    """Footwear Schema - A footwear item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Footwear$")
    name: str
    physical_description: str = Field(description="A physical description of the footwear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a pair of black leather boots with a shiny finish and a thick sole",
        "a pair of white sneakers with a colorful design and a cushioned sole",
        "a pair of brown sandals with a woven strap and a comfortable footbed",
        "a pair of red high heels with a pointed toe and a stiletto heel",
        "a pair of blue flip-flops with a rubber sole and a soft strap",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the shoe rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    covers_feet: bool = Field(description="Whether the footwear covers the feet or not. Should be a boolean value.", examples=[True,False])

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "covers_feet": self.covers_feet
        })
        return json_out

    @staticmethod
    def from_json(data: dict) -> "Footwear":
        """Deserialize a JSON object into a Footwear instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Footwear(**data)