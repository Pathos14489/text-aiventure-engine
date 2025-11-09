from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class Accessory(BaseItem):
    """Accessory Schema - An accessory item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Accessory$")
    name: str
    physical_description: str = Field(description="A physical description of the accessory that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a beautiful necklace with a diamond pendant",
        "a pair of stylish sunglasses",
        "a fancy watch with a leather strap",
        "a delicate bracelet with a charm",
        "a pair of earrings with a pearl",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the accessory rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "type_string": self.type_string,
            "name": self.name,
            "physical_description": self.physical_description,
            "position_in_location": self.position_in_location
        })
        return json_out

    @staticmethod
    def from_json(data: dict) -> "Accessory":
        """Deserialize a JSON object into an Accessory instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Accessory(**data)