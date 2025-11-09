from pydantic import BaseModel, Field
from typing import Union

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class Food(BaseItem):
    """Food Schema - A food item in a text adventure game. All fields are required to have a value. The hunger restored should be a number between 0 and 100, representing the percentage of hunger restored by eating the food. Only Food Items should have a health restored, hunger restored and thirst restored value."""
    type_string: str = Field(description="The type of item.", pattern="^Food$")
    name: str
    physical_description: str = Field(description="A physical description of the food that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a baguette with a crispy crust and soft interior",
        "a ripe banana with a smooth peel and sweet flesh",
        "a juicy apple with a shiny red skin and crisp texture",
        "a slice of pizza with gooey cheese and savory toppings",
        "a bowl of cereal with crunchy flakes and creamy milk",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "In the pantry",
        "On the table",
        "In the fridge",
        "On the shelf",
        "In the cupboard",
        "On the floor"
    ], pattern=lower_single_sentence)
    health_restored: int = Field(...,ge=0,le=100)
    hunger_restored: int = Field(...,ge=0,le=100)
    thirst_restored: int = Field(...,ge=0,le=100)

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "health_restored": self.health_restored,
            "hunger_restored": self.hunger_restored,
            "thirst_restored": self.thirst_restored
        })
        return json_out
    
    @staticmethod
    def from_json(data: dict) -> "Food":
        """Deserialize a JSON object into a Food instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Food(**data)