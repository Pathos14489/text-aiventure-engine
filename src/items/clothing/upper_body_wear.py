from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class UpperBodywear(BaseItem):
    """UpperBodywear Schema - A upperbodywear item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^UpperBodywear$")
    name: str
    physical_description: str = Field(description="A physical description of the upperbodywear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a comfortable t-shirt with a fun print and a relaxed fit",
        "a stylish blouse with a fitted design and a floral pattern",
        "a warm sweater with a chunky knit and a cozy feel",
        "a sleek jacket with a tailored fit and a shiny finish",
        "a sporty hoodie with a loose fit and a kangaroo pocket",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the shirt rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    covers_breasts: bool = Field(description="Whether the upperbodywear covers the chest/breasts or not. Should be a boolean value. A skimpy bikini would cover the chest so long as nipples aren't visible. But it would not cover the belly.", examples=[True,False])
    covers_belly: bool = Field(description="Whether the upperbodywear covers the belly or not. Should be a boolean value. A crop top/bikini would cover the chest easily. But it would not cover the belly. A T-Shirt would cover both however.", examples=[True,False])

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "covers_breasts": self.covers_breasts,
            "covers_belly": self.covers_belly
        })
        return json_out

    @staticmethod
    def from_json(data: dict) -> "UpperBodywear":
        """Deserialize a JSON object into a UpperBodywear instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return UpperBodywear(**data)