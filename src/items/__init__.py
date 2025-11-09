from pydantic import BaseModel, Field
from typing import Union

from src.regex_patterns import lower_single_sentence
from .base_item import BaseItem
from .medical_item import MedicalItem
from .readable.book import Book
from .weapon import Weapon
from .food import Food
from .clothing import Headwear, Footwear, Gloves, LowerBodywear, UpperBodywear, FullBodywear, Accessory, UpperBodyUnderwear, LowerUnderwear

from src.utils import generate_id, preprocess

class Item(BaseItem):
    """Item Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc."""
    id: str = Field(default_factory=generate_id)
    type_string: str = Field(description="The type of item.", pattern="^Item$")
    name: str
    physical_description: str = Field(description="A physical description of the item that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a coffee mug with a blue and white design",
        "a small box with a red lid and a white base",
        "a wooden chair with a cushioned seat and backrest",
        "a large table with a glass top and metal legs",
        "a cardboard box with a brown color and a lid",
    ], pattern=lower_single_sentence)
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
    def from_json(data: dict) -> "Item":
        """Deserialize a JSON object into an Item instance."""
        if "id" not in data:
            data["id"] = generate_id()
        data = preprocess(data)
        return Item(**data)


class Item_Prompt(BaseModel):
    """Item Prompt Schema - A prompt for an item in a text adventure game. All fields are required to have a value."""
    prompt_type: str = Field(description="The type of prompt.", pattern="^Item$")
    prompt: str = Field(description="The prompt for the item.", min_length=1, examples=[
        "A shiny sword.",
        "A rusty dagger.",
        "A magical staff.",
        "A healing potion.",
        "A mysterious amulet."
    ], pattern="^[A-Za-z0-9 ]*$")

    def to_json(self):
        return {
            "prompt_type": self.prompt_type,
            "prompt": self.prompt
        }

    def from_json(data: dict) -> "Item_Prompt":
        """Deserialize a JSON object into an Item_Prompt instance."""
        return Item_Prompt(**data)


class Container(BaseItem):
    """Arbitrary container object for items, characters, or locations. Can be used to store any of the above. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Container$")
    name: str
    physical_description: str = Field(description="A physical description of the container that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a large wooden chest with a rusty lock and a faded red paint",
        "a small cardboard box with a label on the front and a torn corner",
        "a metal safe with a combination lock and a shiny finish",
        "a plastic bin with a lid and a clear front",
        "a wicker basket with a handle and a colorful lining",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    items: list[Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,FullBodywear,Accessory,MedicalItem,Book,UpperBodyUnderwear,LowerUnderwear]] = Field(description="A list of items contained within the container.")
    # value: int = Field(...,ge=0)
    # weight: int = Field(...,ge=0)
    container_value: int = Field(...,ge=0, description="The value of the container itself, not including the items inside it.")
    container_weight: int = Field(...,ge=0, description="The weight of the container itself, not including the items inside it.")

    @property
    def value(self) -> int:
        """Calculate the total value of the container based on the value of the items it contains."""
        return sum(item.value for item in self.items)
    
    @property
    def weight(self) -> int:
        """Calculate the total weight of the container based on the weight of the items it contains and the container weight itself."""
        return sum(item.weight for item in self.items) + self.container_weight
    
    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "items": [item.to_json() for item in self.items],
            "container_value": self.container_value,
            "container_weight": self.container_weight
        })
        del json_out["value"]
        del json_out["weight"]
        return json_out

    @staticmethod
    def from_json(data: dict) -> "Container":
        """Deserialize a JSON object into a Container instance."""
        if "id" not in data:
            data["id"] = generate_id()
        items = data.get("items", [])
        del data["items"]
        container = Container(**data)
        container.items = [from_json(item_data) for item_data in items]
        return container

SomeItem = Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,FullBodywear,Accessory,Container,MedicalItem,Book,UpperBodyUnderwear,LowerUnderwear]

def from_json(data: dict) -> SomeItem:
    """Deserialize a JSON object into the appropriate Item subclass based on the type_string field."""
    type_string = data.get("type_string")
    if type_string == "Item":
        return Item.from_json(data)
    elif type_string == "Food":
        return Food.from_json(data)
    elif type_string == "Weapon":
        return Weapon.from_json(data)
    elif type_string == "Headwear":
        return Headwear.from_json(data)
    elif type_string == "Footwear":
        return Footwear.from_json(data)
    elif type_string == "Gloves":
        return Gloves.from_json(data)
    elif type_string == "LowerBodywear":
        return LowerBodywear.from_json(data)
    elif type_string == "UpperBodywear":
        return UpperBodywear.from_json(data)
    elif type_string == "FullBodywear":
        return FullBodywear.from_json(data)
    elif type_string == "Accessory":
        return Accessory.from_json(data)
    elif type_string == "Container":
        return Container.from_json(data)
    elif type_string == "MedicalItem":
        return MedicalItem.from_json(data)
    elif type_string == "Book":
        return Book.from_json(data)
    elif type_string == "UpperBodyUnderwear":
        return UpperBodyUnderwear.from_json(data)
    elif type_string == "LowerUnderwear":
        return LowerUnderwear.from_json(data)
    else:
        raise ValueError(f"Unknown item type: {type_string}")