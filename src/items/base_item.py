from pydantic import BaseModel, Field
from typing import Union

from src.regex_patterns import lower_single_sentence
from src.utils import generate_id, preprocess

class BaseItem(BaseModel):
    """BaseItem Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc. Items can also be food or weapons, which have additional fields. Only Food Items should have a hunger restored and thirst restored value. Only Weapon Items should have a damage value and required Attributes/Skills to use."""
    id: str = Field(default_factory=generate_id)
    type_string: str = Field(description="The type of item.", examples=[
        "Item",
        "Food",
        "Weapon"
    ], pattern="^(Item|Food|Weapon)$")
    name: str
    physical_description: str = Field(description="A physical description of the item that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the table",
        "In the chest",
        "Under the bed",
        "On the shelf",
        "In the cupboard",
        "On the floor"
    ], pattern=lower_single_sentence)
    value: int = Field(...,ge=0)
    weight: int = Field(...,ge=0)

    def __init__(self, **data):
        data = preprocess(data)
        super().__init__(**data)

    def to_json(self):
        return {
            "id": self.id,
            "type_string": self.type_string,
            "name": self.name,
            "physical_description": self.physical_description,
            "position_in_location": self.position_in_location,
            "value": self.value,
            "weight": self.weight
        }
    
    @staticmethod
    def from_json(data: dict) -> "BaseItem":
        """Deserialize a JSON object into a BaseItem instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return BaseItem(**data)