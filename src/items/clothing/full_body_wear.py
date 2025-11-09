from pydantic import Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class FullBodywear(BaseItem):
    """FullBodywear Schema - A fullbodywear item in a text adventure game. All fields are required to have a value. Fullbodywear can be a dress, a jumpsuit, a suit, etc."""
    type_string: str = Field(description="The type of item.", pattern="^FullBodywear$")
    name: str
    physical_description: str = Field(description="A physical description of the fullbodywear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a onesie with a fun print and a comfortable fit",
        "a stylish dress with a fitted bodice and a flared skirt",
        "a warm jumpsuit with a cozy feel and a zip-up front",
        "a sleek suit with a tailored fit and a shiny finish",
        "a sporty tracksuit with a loose fit and a zip-up jacket",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the dress rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    covers_breasts: bool = Field(description="Whether the fullbodywear covers the chest/breasts or not. Should be a boolean value. A skimpy bikini would cover the chest so long as nipples aren't visible. But it would not cover the belly.", examples=[True,False])
    covers_belly: bool = Field(description="Whether the fullbodywear covers the belly or not. Should be a boolean value. A crop top/bikini would cover the chest easily. But it would not cover the belly. A T-Shirt would cover both however.", examples=[True,False])
    covers_legs: bool = Field(description="Whether the fullbodywear covers the legs or not. Should be a boolean value.", examples=[True,False])
    covers_genitals: bool = Field(description="Whether the fullbodywear covers the genitals or not. Should be a boolean value.", examples=[True,False])
    covers_butt: bool = Field(description="Whether the fullbodywear covers the butt or not. Should be a boolean value.", examples=[True,False])

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "covers_breasts": self.covers_breasts,
            "covers_belly": self.covers_belly,
            "covers_legs": self.covers_legs,
            "covers_genitals": self.covers_genitals,
            "covers_butt": self.covers_butt
        })
        return json_out

    @staticmethod
    def from_json(data: dict) -> "FullBodywear":
        """Deserialize a JSON object into a FullBodywear instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return FullBodywear(**data)