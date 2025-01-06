import json
from openai import OpenAI
import json
from pydantic import BaseModel,Field
from typing import Union, Annotated, Optional
# import gradio as gr
# import threading
from message_formatter import MessageFormatter, PromptStyle
from get_schema_description import get_schema_description
# import time
# import random
# import chromadb
# from chromadb.config import Settings
# import requests
# import bs4
# from bs4 import BeautifulSoup
# import uuid
import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

default_formatter = MessageFormatter()

class SPECIALAttributes(BaseModel):
    """SPECIAL Stats for a character, 1-10"""
    strength: int = Field(ge=1, le=10)
    perception: int = Field(ge=1, le=10)
    endurance: int = Field(ge=1, le=10)
    charisma: int = Field(ge=1, le=10)
    intelligence: int = Field(ge=1, le=10)
    agility: int = Field(ge=1, le=10)
    luck: int = Field(ge=1, le=10)

class Stats(BaseModel):
    """Stats for a character"""
    hp: int = Field(100, ge=0, description="The character's health points. This is used for things like how much damage the character can take before dying, etc.")
    hunger: int = Field(100, ge=0, le=100, description="The character's hunger level. This is used for things like how hungry the character is, how much they need to eat, etc.")
    thirst: int = Field(100, ge=0, le=100, description="The character's thirst level. This is used for things like how thirsty the character is, how much they need to drink, etc.")

class TravelableLocation(BaseModel):
    """Travelable Location Schema - A location in a text adventure game that can be traveled to. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Setting, Atmosphere, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Tags are used to help search for locations, and can be things like "Forest", "Castle", "Desert", etc. All fields are required to have a value. These should be physically connected locations to the Location parent that they are a part of. Examples of travelable locations include doors, gates, paths, etc. that lead to other nearby locations. The manner in which the characters travel to a new location. Travelable locations can only be large spaces, and CANNOT be objects within the current location."""
    # location_type: str = Field(description="The type of location.", pattern="^(Indoors|Outdoors)$")
    portal: str = Field(description="The name of the portal that leads to this location. Can be a door, a gate, a hole in the ground, an actual portal, etc. The manner in which the characters travel to the new location. ", examples=[
        "The Door to the Kitchen",
        "A small path into the forest",
        "A large set of double doors",
        "Door leading outside",
        "Door to the Bee and Barb",
        "The Front Door"
    ])
    location_name: str = Field(description="The name of the location. Can be a city, a forest, a mountain, a cave, etc. The name of the location.", examples=[
        "Kitchen - Your House",
        "The Forest of Shadows - East Entrance",
        "The Castle of the Mad King - Throne Room",
        "Time Square - New York City",
        "The Bee and Barb",
        "City Square - Whiterun"
    ])
    location_description: str = Field(description="A brief description of the location. Can be a city, a forest, a mountain, a cave, etc. The description of the location.", examples=[
        "A small kitchen in your house",
        "A dark and foreboding forest",
        "A grand throne room in a castle",
        "A bustling city square",
        "A cozy inn",
        "A large bustling city square in the middle of the day"
    ])
    movement_description: str = Field(description="A description of how the characters move to the new location. Can be via a door, a gate, a path, etc. The manner in which the characters travel to the new location.", examples=[
        "You walk through the door",
        "You step through the portal",
        "You walk down the path",
        "You walk through the gate",
        "You step through the archway",
        "You walk through the tunnel"
    ])

class BaseItem(BaseModel):
    """BaseItem Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc. Items can also be food or weapons, which have additional fields. Only Food Items should have a hunger restored and thirst restored value. Only Weapon Items should have a damage value and required SPECIAL stats."""
    type_string: str = Field(description="The type of item.", examples=[
        "Item",
        "Food",
        "Weapon"
    ], pattern="^(Item|Food|Weapon)$")
    name: str
    physical_description: str = Field(description="A description of the item. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.")
    value: int = Field(...,ge=0)
    weight: int = Field(...,ge=0)

class Item(BaseItem):
    """Item Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc."""
    type_string: str = Field(description="The type of item.", pattern="^Item$")
    name: str
    physical_description: str = Field(description="A description of the item. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the table",
        "In the chest",
        "Under the bed",
        "On the shelf",
        "In the cupboard",
        "On the floor"
    ])
    value: int = Field(...,ge=0)
    weight: int = Field(...,ge=0)

class Food(BaseItem):
    """Food Schema - A food item in a text adventure game. All fields are required to have a value. The hunger restored should be a number between 0 and 100, representing the percentage of hunger restored by eating the food. Only Food Items should have a health restored, hunger restored and thirst restored value."""
    type_string: str = Field(description="The type of item.", pattern="^Food$")
    name: str
    physical_description: str = Field(description="A description of the food. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "In the pantry",
        "On the table",
        "In the fridge",
        "On the shelf",
        "In the cupboard",
        "On the floor"
    ])
    health_restored: int = Field(...,ge=0,le=100)
    hunger_restored: int = Field(...,ge=0,le=100)
    thirst_restored: int = Field(...,ge=0,le=100)

class Weapon(BaseItem):
    """Weapon Schema - A weapon item in a text adventure game. Unless a weapon is super complicated, most requirements should be below 5. Anything over 5 for a required SPECIAL stat is considered very high, and should be reserved for very powerful weapons. Only Weapon Items should have a damage value and required SPECIAL stats."""
    type_string: str = Field(description="The type of item.", pattern="^Weapon$")
    name: str
    physical_description: str = Field(description="A description of the weapon. Should be at least a sentence long.")
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the gun rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])
    damage: int = Field(...,description="The amount of damage the weapon does. Should be a number between 0 and 100, but can go higher if you want to be extra.")
    strength_required: int = Field(...,description="The amount of strength required to wield the weapon. Should be a number between 1 and 10.")
    perception_required: int = Field(...,description="The amount of perception required to wield the weapon. Should be a number between 1 and 10.")
    endurance_required: int = Field(...,description="The amount of endurance required to wield the weapon. Should be a number between 1 and 10.")
    charisma_required: int = Field(...,description="The amount of charisma required to wield the weapon. Should be a number between 1 and 10.")
    intelligence_required: int = Field(...,description="The amount of intelligence required to wield the weapon. Should be a number between 1 and 10.")
    agility_required: int = Field(...,description="The amount of agility required to wield the weapon. Should be a number between 1 and 10.")
    luck_required: int = Field(...,description="The amount of luck required to wield the weapon. Should be a number between 1 and 10.")

class Headwear(BaseItem):
    """Headwear Schema - A headwear item in a text adventure game. All fields are required to have a value. Only Clothing Items should have a warmth value."""
    type_string: str = Field(description="The type of item.", pattern="^Headwear$")
    name: str
    physical_description: str = Field(description="A description of the headwear. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the hat rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])
    covers_hair: bool = Field(description="Whether the headwear covers the hair or not. Should be a boolean value.", examples=[True,False])
    covers_face: bool = Field(description="Whether the headwear covers the face or not. Should be a boolean value.", examples=[True,False])

class Footwear(BaseItem):
    """Footwear Schema - A footwear item in a text adventure game. All fields are required to have a value. Only Clothing Items should have a warmth value."""
    type_string: str = Field(description="The type of item.", pattern="^Footwear$")
    name: str
    physical_description: str = Field(description="A description of the footwear. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the shoe rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])
    covers_feet: bool = Field(description="Whether the footwear covers the feet or not. Should be a boolean value.", examples=[True,False])

class Gloves(BaseItem):
    """Gloves Schema - A gloves item in a text adventure game. All fields are required to have a value. Only Clothing Items should have a warmth value."""
    type_string: str = Field(description="The type of item.", pattern="^Gloves$")
    name: str
    physical_description: str = Field(description="A description of the gloves. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the glove rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])

class LowerBodywear(BaseItem):
    """LowerBodywear Schema - A lowerbodywear item in a text adventure game. All fields are required to have a value. Only Clothing Items should have a warmth value."""
    type_string: str = Field(description="The type of item.", pattern="^LowerBodywear$")
    name: str
    physical_description: str = Field(description="A description of the lowerbodywear. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the pants rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])
    covers_legs: bool = Field(description="Whether the lowerbodywear covers the legs or not. Should be a boolean value.", examples=[True,False])
    covers_genitals: bool = Field(description="Whether the lowerbodywear covers the genitals or not. Should be a boolean value.", examples=[True,False])
    covers_butt: bool = Field(description="Whether the lowerbodywear covers the butt or not. Should be a boolean value.", examples=[True,False])

# class TopUnderwear(BaseItem):
#     """Underwear Schema - An underwear item in a text adventure game. All fields are required to have a value. Only Clothing Items should have a warmth value."""
#     type_string: str = Field(description="The type of item.", pattern="^TopUnderwear$")
#     name: str = Field(description="The name of the underwear.", examples=[
#         "Bra",
#         "Panties",
#         "Red Bikini Top",
#         "Sports Bra"
#     ])
#     physical_description: str = Field(description="A description of the underwear. Should be at least a sentence long.", min_length=1)
#     position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
#         "On the underwear rack",
#         "On the table",
#         "In the chest",
#         "On the shelf",
#         "Beside the sandbags",
#         "On the ground"
#     ])

# class BottomUnderwear(BaseItem):
#     """Lower Underwear Schema - An underwear item in a text adventure game. All fields are required to have a value. Only Clothing Items should have a warmth value. Underwear can also be a swimsuit, or other undergarments."""
#     type_string: str = Field(description="The type of item.", pattern="^BottomUnderwear$")
#     name: str = Field(description="The name of the underwear.", examples=[
#         "Boxers",
#         "Briefs",
#         "Red Bikini Bottom",
#         "Thong"
#     ])
#     physical_description: str = Field(description="A description of the underwear. Should be at least a sentence long.", min_length=1)
#     position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
#         "On the underwear rack",
#         "On the table",
#         "In the chest",
#         "On the shelf",
#         "Beside the sandbags",
#         "On the ground"
#     ])


class UpperBodywear(BaseItem):
    """UpperBodywear Schema - A upperbodywear item in a text adventure game. All fields are required to have a value. Only Clothing Items should have a warmth value."""
    type_string: str = Field(description="The type of item.", pattern="^UpperBodywear$")
    name: str
    physical_description: str = Field(description="A description of the upperbodywear. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the shirt rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])
    covers_breasts: bool = Field(description="Whether the upperbodywear covers the chest/breasts or not. Should be a boolean value. A skimpy bikini would cover the chest so long as nipples aren't visible. But it would not cover the belly.", examples=[True,False])
    covers_belly: bool = Field(description="Whether the upperbodywear covers the belly or not. Should be a boolean value. A crop top/bikini would cover the chest easily. But it would not cover the belly. A T-Shirt would cover both however.", examples=[True,False])
    full_body_suit: bool = Field(description="Whether the upperbodywear covers the entire body or not. Should be a boolean value. A full body suit would cover the entire body, including the arms, legs, and head.", examples=[True,False])

class Accessory(BaseItem):
    """Accessory Schema - An accessory item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Accessory$")
    name: str
    physical_description: str = Field(description="A description of the accessory. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the accessory rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])

class Equipment(BaseModel):
    """Equipment Schema - A set of equipment in a text adventure game. The equipment is a set of items that the player can wear, and should include a headwear, footwear, gloves, lowerbodywear, and upperbodywear item. Not all fields are required to have a value. If a character doesn't have a slot equiped, it should be None."""
    headwear: Union[Headwear,None] = Field(description="The headwear that the character has equiped. If the character has no headwear equiped, this whole object should be null.")
    upperbodywear: Union[UpperBodywear,None] = Field(description="The upperbodywear that the character has equiped. If the character has no upperbodywear equiped, this whole object should be null.")
    # top_underwear: Union[TopUnderwear,None] = Field(description="The underwear that the character has equiped. If the character has no underwear equiped, this whole object should be null.")
    gloves: Union[Gloves,None] = Field(description="The gloves that the character has equiped. If the character has no gloves equiped, this whole object should be null.")
    # bottom_underwear: Union[BottomUnderwear,None] = Field(description="The underwear that the character has equiped. If the character has no underwear equiped, this whole object should be null.")
    lowerbodywear: Union[LowerBodywear,None] = Field(description="The lowerbodywear that the character has equiped. If the character has no lowerbodywear equiped, this whole object should be null.")
    footwear: Union[Footwear,None] = Field(description="The footwear that the character has equiped. If the character has no footwear equiped, this whole object should be null.")
    equiped_weapon: Union[Weapon,None] = Field(description="The weapon that the character has equiped. If the character has no weapon equiped, this whole object should be null.")
    accessories: list[Accessory] = Field(description="A list of accessories that the character has on them. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required SPECIAL stats. If an item is a weapon, it MUST have a damage value and required SPECIAL stats. If an item is food, it MUST have a hunger restored and thirst restored value. This is not worn equipment, but items that the character has in their inventory.")
    inventory: list[Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory]] = Field(description="A list of objects that the character has on them. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required SPECIAL stats. If an item is a weapon, it MUST have a damage value and required SPECIAL stats. If an item is food, it MUST have a hunger restored and thirst restored value. This is not worn equipment, but items that the character has in their inventory. To be in a characters inventory, they must be actively carrying the item. Items in the inventory are not equiped, and are not being worn by the character. They CANNOT be on the ground, in a box, on a table, etc. They MUST be in the character's possession on their person.")

class BodyPartDescriptions(BaseModel):
    """Body Part Descriptions Schema - A set of descriptions for a character's body parts. Should not describe their clothes or equipment in any way. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that they should cohesively flow together, seperated by new lines, and not repeat themselves. All fields are required to have a value. Body part descriptions should only use the characters gender to refer to them, never by name. Example: \"She has a cute face.\""""
    hair_description: str = Field(...,description="A description of the character's hair. Should be at least a paragraph long and explicitly and graphically describe the character's hair.", min_length=1, examples=[
        "She has long, flowing, blonde hair that cascades down her back in gentle waves."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    face_description: str = Field(...,description="A description of the character's face. Should be at least a paragraph long and explicitly and graphically describe the character's nude face.", min_length=1, examples=[
        "She has a cute face with big, bright eyes and a small, upturned nose."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    bare_chest_description: str = Field(...,description="A description of the character's chest without clothes. Should be at least a paragraph long and explicitly and graphically describe the character's nude chest.", min_length=1, examples=[
        "She has a perky pair of breasts with small, pink nipples that stand out against her pale skin."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    abdomen_description: str = Field(...,description="A description of the character's abdomen not including the chest or genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude body.", min_length=1, examples=[
        "Her abdomen is flat and toned, with a small belly button in the center."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    genital_description: str = Field(...,description="A description of the character's genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude genitals.", min_length=1, examples=[
        "She has a small, neatly trimmed bush of pubic hair above her pussy, which is small and tight."
    ], pattern="^(His|Her|He|She|Between)([A-Za-z0-9 ])*$")
    butt_description: str = Field(...,description="A description of the character's butt. Should be at least a paragraph long and explicitly and graphically describe the character's nude butt.", min_length=1, examples=[
        "She has a perky, round butt that looks great in a pair of tight jeans."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    legs_description: str = Field(...,description="A description of the character's legs. Should be at least a paragraph long and explicitly and graphically describe the character's nude legs.", min_length=1, examples=[
        "She has long, toned legs that look great in a pair of shorts."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    arms_description: str = Field(...,description="A description of the character's arms. Should be at least a paragraph long and explicitly and graphically describe the character's nude arms.", min_length=1, examples=[
        "She has long, slender arms with delicate hands and long fingers."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    hands_description: str = Field(...,description="A description of the character's hands. Should be at least a paragraph long and explicitly and graphically describe the character's nude hands.", min_length=1, examples=[
        "She has small, delicate hands with long fingers and neatly trimmed nails."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    feet_description: str = Field(...,description="A description of the character's feet. Should be at least a paragraph long and explicitly and graphically describe the character's nude feet.", min_length=1, examples=[
        "She has small, dainty feet with high arches and neatly painted toenails."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")

class Character(BaseModel):
    """Character Schema - No stats, just descriptions. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Personality, Appearance, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Drives are what motivates the character, and can be things like "Revenge on the bandits who killed their family" or "To find the lost city of gold". Tags are used to help search for characters, and can be things like "Elf", "Wizard", "Pirate", etc. The voice description is seperate from the other descriptions, and should be able to exist by itself without the other descriptions. It should describe how the character should sound. All descriptions should be at least a paragraph long, and the first message should be at least a sentence long, but longer is not bad. The backstory is the character's history, and should be at least a paragraph long. The naked body description is what the character looks like without clothes, and should be at least a paragraph long and explicitly and graphically describe the character's nude body. All fields are required to have a value."""
    full_name: str
    nick_name: str
    age: int = Field(...)
    gender: str = Field(...,examples=["Male","Female"],pattern="^(Male|Female)$")
    race: str
    species: str
    special_attributes: SPECIALAttributes
    stats: Stats = None
    equipment: Equipment
    hex_color: str = Field(...,description="The hex color code for the character's name. Should be a 6 character hex code, without the #.",pattern="^([0-9A-Fa-f]{6})$")
    personality_description: str
    body_part_desctiptions: BodyPartDescriptions
    backstory: str = Field(...,description="A description of the character's backstory. Should be at least a paragraph long.", min_length=1)

    def __init__(self, **data):
        super().__init__(**data)
        self.stats = Stats(hp=100,hunger=100,thirst=100)

    def get_age(self):
        if self.age < 5:
            return "toddler"
        elif self.age < 13:
            return "child"
        elif self.age < 18:
            return "teenager"
        elif self.age < 30:
            return "young adult"
        elif self.age < 50:
            return "adult"
        else:
            return "elderly"
        
    def get_aged_gender(self):
        age_str = self.get_age()
        if self.gender == "Male":
            if age_str == "child":
                return "little boy"
            elif age_str == "teenager":
                return "boy"
            elif age_str == "young adult" or age_str == "adult" or age_str == "elderly":
                return "man"
        elif self.gender == "Female":
            if age_str == "child":
                return "little girl"
            elif age_str == "teenager":
                return "girl"
            elif age_str == "young adult" or age_str == "adult" or age_str == "elderly":
                return "woman"
        return "person"
    
    def get_pronouns(self):
        if self.gender == "Male":
            return {
                "subject": "he",
                "object": "him",
                "possessive": "his",
                "possessive_pronoun": "his",
                "reflexive": "himself"
            }
        else:
            return {
                "subject": "she",
                "object": "her",
                "possessive": "her",
                "possessive_pronoun": "hers",
                "reflexive": "herself"
            }

    def get_description(self):
        return f"{self.full_name.strip()} is a {str(self.age).strip()} year old {self.get_aged_gender()}. {self.get_pronouns()['subject'].capitalize()} is a {self.race.strip()} {self.species.strip()}. {self.personality_description.strip()} {self.backstory.strip()}"
    
    def get_unknown_description(self, capitalize=False):
        if capitalize:
            description = f"A"
        else:
            description = f"a"
        if self.race.lower().strip() != "":
            description += f" {self.race.lower().strip()}"
        if self.species.lower().strip() != "":
            description += f" {self.species.lower().strip()}"
        return f"{description.strip()} {self.get_aged_gender().strip()}".strip()
    
    def get_physical_description(self):
        # return physical appearance accounting for equipment
        description = ""
        wearing_full_body_suit = False
        if self.equipment.headwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.headwear.physical_description}\n"
            if not self.equipment.headwear.covers_hair:
                description += f"{self.body_part_desctiptions.hair_description}\n"
            if not self.equipment.headwear.covers_face:
                description += f"{self.body_part_desctiptions.face_description}\n"
        else:
            description += f"{self.body_part_desctiptions.hair_description}\n"
        if self.equipment.upperbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.upperbodywear.physical_description[0].lower()}{self.equipment.upperbodywear.physical_description[1:]}\n"
            if not self.equipment.upperbodywear.covers_breasts:
                description += f"{self.body_part_desctiptions.bare_chest_description}\n"
            if not self.equipment.upperbodywear.covers_belly:
                description += f"{self.body_part_desctiptions.abdomen_description}\n"
            if self.equipment.upperbodywear.full_body_suit:
                wearing_full_body_suit = True
        else:
            description += f"{self.body_part_desctiptions.bare_chest_description}\n"
        if self.equipment.gloves:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.gloves.physical_description[0].lower()}{self.equipment.gloves.physical_description[1:]}\n"
        else:
            description += f"{self.body_part_desctiptions.hands_description}\n"
        if self.equipment.lowerbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.lowerbodywear.physical_description[0].lower()}{self.equipment.lowerbodywear.physical_description[1:]}\n"
            if not self.equipment.lowerbodywear.covers_legs and not wearing_full_body_suit:
                description += f"{self.body_part_desctiptions.legs_description}\n"
            if not self.equipment.lowerbodywear.covers_genitals and not wearing_full_body_suit:
                description += f"{self.body_part_desctiptions.genital_description}\n"
            if not self.equipment.lowerbodywear.covers_butt and not wearing_full_body_suit:
                description += f"{self.body_part_desctiptions.butt_description}\n"
        else:
            if not wearing_full_body_suit:
                description += f"{self.body_part_desctiptions.legs_description}\n"
                description += f"{self.body_part_desctiptions.genital_description}\n"
                description += f"{self.body_part_desctiptions.butt_description}\n"
        if self.equipment.footwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.footwear.physical_description[0].lower()}{self.equipment.footwear.physical_description[1:]}\n"
        else:
            description += f"{self.body_part_desctiptions.feet_description}\n"
        if self.stats.hp <= 0:
            description += f"{self.get_pronouns()['subject'].capitalize()} is dead."
            if self.equipment.equiped_weapon:
                description += f"{self.get_pronouns()['object'].capitalize()} weapon, a {self.equipment.equiped_weapon.physical_description}, is lying on the ground beside {self.get_pronouns()['object']} body."
        else:
            if self.equipment.equiped_weapon:
                description += f"{self.get_pronouns()['subject'].capitalize()} is holding a {self.equipment.equiped_weapon.physical_description}."
        return description.strip()

    def get_equipment_description(self):
        # return equipment description
        description = ""
        if self.equipment.headwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.headwear.physical_description}. "
        if self.equipment.upperbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.upperbodywear.physical_description}. "
        if self.equipment.gloves:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.gloves.physical_description}. "
        if self.equipment.lowerbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.lowerbodywear.physical_description}. "
        if self.equipment.footwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.equipment.footwear.physical_description}. "
        if self.equipment.equiped_weapon:
            description += f"{self.get_pronouns()['subject'].capitalize()} is holding a {self.equipment.equiped_weapon.physical_description}."
        description = description.strip()
        if description == "":
            description = f"{self.get_pronouns()['subject'].capitalize()} is completely naked."
        return description

class Container(BaseItem):
    """Arbitrary container object for items, characters, or locations. Can be used to store any of the above. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Container$")
    name: str
    physical_description: str
    position_in_location: str
    items: list[Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory]]    
    value: int = Field(...,ge=0)
    weight: int = Field(...,ge=0)

class Location(BaseModel):
    """Location Schema - A location in a text adventure game. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that they are all separate sections that should cohesively flow together, seperated by new lines, and not repeat themselves. Tags are used to help search for locations, and can be things like "Forest", "Castle", "Desert", etc. All fields are required to have a value."""
    name: str = Field(description="The name of the location.", min_length=1, examples=[
        "The Dark Cave",
        "The Enchanted Forest",
        "The Haunted Mansion",
        "The Abandoned Town",
        "The Deserted Island",
        "The Lost City"
    ])
    location_physical_description: str = Field(description="A description of the location. Should be at least a paragraph long. MUST NOT contain any information about items or characters in the location. This should strictly be a description of the location without any storytelling involved. No talking about how the player moves, don't include plot elements or thoughts that the player is thinking, merely describe the location as detailedly as possible. This should NOT describe the items or characters in the location, only the physical description of the location itself. If the user's prompt includes objects or characters in the location, they should be described in the objects_in_location and characters_in_location fields ONLY.", min_length=1, examples=[
        "A dark, damp cave with a low ceiling and a musty smell.",
        "A dense, overgrown forest with tall trees and thick underbrush.",
        "A large, spooky mansion with creaky floors and drafty hallways.",
        "An old, abandoned town with crumbling buildings and overgrown streets.",
        "A small, sandy island with palm trees and crystal clear water.",
        "A ruined city with crumbling buildings and twisted metal."
    ])
    travel_destinations: list[TravelableLocation] = Field(description="A list of locations that can be traveled to from this location. Each travelable location should have a portal, location name, and location prompt. All possible travelable locations from this location. If this is in a section of a town for instance, it could have a travelable location to the market, the inn, the blacksmith, travelable locations out of town, travelable locations to the other parts of town, etc. Be detailed when coming up with travelable locations. Travel locations should usually be logical and reasonable. For example, if you're lost in a white void with just a cake, you could do \"Explore the void\" but wouldn't do \"The Cake\" unless the cake was large enough to stand on.", min_length=1)
    objects_in_location: list[Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory]] = Field(description="A list of objects in the location. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required SPECIAL stats. If an item is a weapon, it MUST have a damage value and required SPECIAL stats. If an item is food, it MUST have a hunger restored and thirst restored value.")
    characters_in_location: list[Character] = Field(description="A list of characters in the location.")

class SomeItem(BaseModel):
    """SomeItem Schema - Any item in a text adventure game. All fields are required to have a value."""
    item: Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory]

class Story(BaseModel):
    """Story Schema - A story in a text adventure game. Summarizes the vibe and aesthetic of the story. All fields are required to have a value."""
    # title: str
    # setting: str = Field(description="The setting of the story. Can be a city, a forest, a mountain, a cave, etc.")
    vibe: str = Field(description="The vibe of the story.")
    aesthetic: str = Field(description="The aesthetic of the story. Can be a genre, a theme, a style, etc. The overall feel of the story and the writing of the items, characters, and locations.")
    starting_location: Location = Field(description="The starting location of the story.")

class TextAIventureEngine():
    def __init__(self):
        self.story_title = None
        self.story_setting = None
        self.story_vibe = None
        self.story_aesthetic = None
        self.starting_location = None
        self.locations = []
        self.characters = []
        self.met = []
        self.client = OpenAI(api_key="abc123", base_url="http://localhost:8000/v1/")
        # self.chroma_path = f"./chromadb"
        # self.chroma_client = chromadb.PersistentClient(self.chroma_path,Settings(anonymized_telemetry=False))
        self.temp = 1.12
        self.top_p = 0.95
        self.min_p = 0.075
        self.max_tokens = 3072

    def generate_story(self, prompt:str):
        print("Generating Story for Prompt:",prompt)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a story JSON to run the text adventure game with. It will adhere to the JSON schema for a story, and will be returned as a JSON object. Below is reference for the schema for a story.",
            }
        ]
        schema = Story.model_json_schema()
        schema_description = get_schema_description(schema)
        item_schema = Item.model_json_schema()
        item_schema_description = get_schema_description(item_schema)
        food_schema = Food.model_json_schema()
        food_schema_description = get_schema_description(food_schema)
        weapon_schema = Weapon.model_json_schema()
        weapon_schema_description = get_schema_description(weapon_schema)
        character_schema = Character.model_json_schema()
        character_schema_description = get_schema_description(character_schema)
        messages.append({
            "role": "system",
            "content": f"{schema_description}\n\n{item_schema_description}\n\n{food_schema_description}\n\n{weapon_schema_description}\n\n{character_schema_description}"
        })
        messages.append({
            "role": "user",
            "content": "Generate a story based on the following prompt:"+prompt
        })
        # print(json.dumps(messages,indent=4))
        story = None
        while story == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                story_json = completion.choices[0].message.content
                story_json = json.loads(story_json)
                story = Story(**story_json)
                for character in story.starting_location.characters_in_location:
                    if character.equipment.headwear != None:
                        if character.equipment.headwear.name.lower() == "none" or character.equipment.headwear.name.lower() == "null" or character.equipment.headwear.name.strip() == "":
                            character.equipment.headwear = None
                    if character.equipment.upperbodywear != None:
                        if character.equipment.upperbodywear.name.lower() == "none" or character.equipment.upperbodywear.name.lower() == "null" or character.equipment.upperbodywear.name.strip() == "":
                            character.equipment.upperbodywear = None
                    # if character.equipment.top_underwear != None:
                    #     if character.equipment.top_underwear.name.lower() == "none" or character.equipment.top_underwear.name.lower() == "null" or character.equipment.top_underwear.name.strip() == "":
                    #         character.equipment.top_underwear = None
                    if character.equipment.gloves != None:
                        if character.equipment.gloves.name.lower() == "none" or character.equipment.gloves.name.lower() == "null" or character.equipment.gloves.name.strip() == "":
                            character.equipment.gloves = None
                    # if character.equipment.bottom_underwear != None:
                    #     if character.equipment.bottom_underwear.name.lower() == "none" or character.equipment.bottom_underwear.name.lower() == "null" or character.equipment.bottom_underwear.name.strip() == "":
                    #         character.equipment.bottom_underwear = None
                    if character.equipment.lowerbodywear != None:
                        if character.equipment.lowerbodywear.name.lower() == "none" or character.equipment.lowerbodywear.name.lower() == "null" or character.equipment.lowerbodywear.name.strip() == "":
                            character.equipment.lowerbodywear = None
                    if character.equipment.footwear != None:
                        if character.equipment.footwear.name.lower() == "none" or character.equipment.footwear.name.lower() == "null" or character.equipment.footwear.name.strip() == "":
                            character.equipment.footwear = None
                    if character.equipment.equiped_weapon != None:
                        if character.equipment.equiped_weapon.name.lower() == "none" or character.equipment.equiped_weapon.name.lower() == "null" or character.equipment.equiped_weapon.name.strip() == "":
                            character.equipment.equiped_weapon = None
                    if character.equipment.accessories != None:
                        for item in character.equipment.accessories:
                            if item.name.lower() == "none" or item.name.lower() == "null" or item.name.strip() == "":
                                character.equipment.accessories.remove(item)
                    for item in character.equipment.inventory:
                        if item.name.lower() == "none" or item.name.lower() == "null" or item.name.strip() == "":
                            character.equipment.inventory.remove(item)
                    # overwrite the character with the new one
                    for c in self.characters:
                        if c.full_name == character.full_name:
                            self.characters.remove(c)
                            self.characters.append(character)
                            break
                story_json = json.loads(story.model_dump_json())
                print(json.dumps(story_json,indent=4))
            except Exception as e:
                print(e)
                pass
        return story
    
    def generate_travelling_location(self, previous_location:Location, prompt:str):
        print("Generating Location for Prompt:",prompt)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a location JSON to run the text adventure game with. It will adhere to the JSON schema for a location, and will be returned as a JSON object. Below is reference for the schema for a location.",
            },
            {
                "role": "system",
                "content": f"The previous location was {previous_location.name}.\n{previous_location.location_physical_description}"
            },
            {
                "role": "system",
                "content": f"The setting is {self.story_setting}, the vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = Location.model_json_schema()
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": "Generate a location based on the following prompt:"+prompt
        })
        location = None
        while location == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                location = Location(**location_json)
                print(json.dumps(location_json,indent=4))
            except Exception as e:
                # print(e)
                pass
        return location
    
    def generate_location(self, prompt:str):
        print("Generating Location for Prompt:",prompt)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a location JSON to run the text adventure game with. It will adhere to the JSON schema for a location, and will be returned as a JSON object. Below is reference for the schema for a location.",
            },
            {
                "role": "system",
                "content": f"The setting is {self.story_setting}, the vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = Location.model_json_schema()
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": "Generate a location based on the following prompt:"+prompt
        })
        location = None
        while location == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                location = Location(**location_json)
                print(json.dumps(location_json,indent=4))
            except Exception as e:
                # print(e)
                pass
        return location

    def generate_travelable_location(self, location:Location, prompt:str):
        print("Generating Travelable Location for Prompt:",prompt)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a travelable location JSON to run the text adventure game with. It will adhere to the JSON schema for a travelable location, and will be returned as a JSON object. Below is reference for the schema for a travelable location.",
            },
            {
                "role": "system",
                "content": f"The user is travelling from {location.name}.\n{location.location_physical_description}"
            },
            {
                "role": "system",
                "content": f"The setting is {self.story_setting}, the vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = TravelableLocation.model_json_schema()
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": "Generate the next location based on the following prompt:"+prompt
        })
        travelable_location = None
        while travelable_location == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                travelable_location_json = completion.choices[0].message.content
                travelable_location_json = json.loads(travelable_location_json)
                travelable_location = TravelableLocation(**travelable_location_json)
                print(json.dumps(travelable_location_json,indent=4))
            except Exception as e:
                # print(e)
                pass
        return travelable_location

    def generate_travelable_location_between(self, prev_location:Location, next_location2:Location, previous_method_of_travel:str = None):
        print("Generating Travelable Location between:",prev_location.name,"and",next_location2.name)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a travelable location JSON to run the text adventure game with. It will adhere to the JSON schema for a travelable location, and will be returned as a JSON object. Below is reference for the schema for a travelable location.",
            },
            {
                "role": "system",
                "content": f"The previous location was {prev_location.name}.\n{prev_location.location_physical_description}\nThe next location is {next_location2.name}.\n{next_location2.location_physical_description}"
            },
            {
                "role": "system",
                "content": f"The setting is {self.story_setting}, the vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        if previous_method_of_travel != None:
            messages.append({
                "role": "system",
                "content": f"The previous method of travel was: {previous_method_of_travel}\nThe next movement_description should be the reverse of this."
            })
        schema = TravelableLocation.model_json_schema()
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": f"Generate a travelable location between {prev_location.name} and {next_location2.name}."
        })
        travelable_location = None
        while travelable_location == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                travelable_location_json = completion.choices[0].message.content
                travelable_location_json = json.loads(travelable_location_json)
                travelable_location = TravelableLocation(**travelable_location_json)
                print(json.dumps(travelable_location_json,indent=4))
            except Exception as e:
                # print(e)
                pass
        return travelable_location

    def set_story(self, story:Story):
        # self.story_title = story.title
        # self.story_setting = story.setting
        self.story_vibe = story.vibe
        self.story_aesthetic = story.aesthetic
        self.starting_location = story.starting_location
        self.locations.append(story.starting_location)
    
    def travel_to_location_from(self, previous_location:Location, travelable_location:TravelableLocation):
        next_location = None
        for loc in self.locations:
            if loc.name == travelable_location.location_name:
                next_location = loc
                break
        if next_location == None: # location doesn't exist yet
            next_location = self.generate_location_from_travelable_location(previous_location, travelable_location) # generate the location
            next_location.name = travelable_location.location_name
            self.locations.append(next_location)
        can_travel = False
        for t_location in previous_location.travel_destinations:
            if t_location.portal == travelable_location.portal:
                can_travel = True
                break
        if can_travel:
            already_has_between_location = False
            for travelable_l in next_location.travel_destinations:
                if travelable_l.location_name == previous_location.name:
                    # print("Already has a travelable location between",previous_location.name,"and",location.name)
                    already_has_between_location = True
                    break
            if not already_has_between_location: 
                portal_already_exists = False
                while not portal_already_exists:
                    between_location = self.generate_travelable_location_between(next_location, previous_location, travelable_location.movement_description)
                    for t_location in previous_location.travel_destinations:
                        if t_location.portal == between_location.portal:
                            portal_already_exists = True
                            break
                    if not portal_already_exists:
                        between_location.location_name = previous_location.name
                        next_location.travel_destinations.append(between_location)
                        portal_already_exists = True
            # print(f"Travelling to {next_location.name}...")
            print(travelable_location.movement_description)
            # When travelling to a location, make sure you can't travel to the same location from that location
            for t_location in next_location.travel_destinations:
                if t_location.location_name == next_location.name:
                    next_location.travel_destinations.remove(t_location)
                    break
            return next_location
        else:
            print("You can't travel to that location from here!")
            return previous_location
        
    def generate_location_from_travelable_location(self, current_location:Location, travelable_location:TravelableLocation):
        print("Generating Location from Travelable Location:",travelable_location.location_name)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a location JSON to run the text adventure game with. It will adhere to the JSON schema for a location, and will be returned as a JSON object. Below is reference for the schema for a location.",
            },
            {
                "role": "system",
                "content": f"The previous location was {current_location.name}.\n{current_location.location_physical_description}"
            },
            {
                "role": "system",
                "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = Location.model_json_schema()
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": "Generate a location based on the following prompt:"+travelable_location.location_description
        })
        location = None
        while location == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                location = Location(**location_json)
                print(json.dumps(location_json,indent=4))
            except Exception as e:
                # print(e)
                pass
        return location

    def generate_character_from_prompt(self, prompt:str):
        print("Generating Character for Prompt:",prompt)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a character JSON to run the text adventure game with. It will adhere to the JSON schema for a character, and will be returned as a JSON object. Below is reference for the schema for a character.",
            }
        ]
        schema = Character.model_json_schema()
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": "Generate a character based on the following prompt:"+prompt
        })
        character = None
        while character == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                character_json = completion.choices[0].message.content
                character_json = json.loads(character_json)
                character = Character(**character_json)
                print(json.dumps(character_json,indent=4))
            except Exception as e:
                # print(e)
                pass
        return character
    
    def generate_item_from_prompt(self, prompt:str):
        print("Generating Item for Prompt:",prompt)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating an item JSON to run the text adventure game with. It will adhere to the JSON schema for an item, and will be returned as a JSON object. Below is reference for the schema for an item.",
            }
        ]
        schema = SomeItem.model_json_schema()
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": "Generate an item based on the following prompt:"+prompt
        })
        item = None
        while item == None:
            try:
                completion = self.client.chat.completions.create(
                    model="L3-8B-Stheno-v3.2-Q6_K",
                    messages=messages,
                    temperature=self.temp,
                    top_p=self.top_p,
                    extra_body={
                        # "grammar": schema,
                        "response_format":{
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                item_json = completion.choices[0].message.content
                item_json = json.loads(item_json)
                item = SomeItem(**item_json)
                item = item.item
                item.position_in_location = "on the ground"
                print(json.dumps(json.loads(item.model_dump_json()),indent=4))
            except Exception as e:
                # print(e)
                pass
        return item

text_adventure = TextAIventureEngine()
ready = False
while not ready:
    prompt = input("Enter a prompt for the story generation: ")
    story = text_adventure.generate_story(prompt)
    confirmation = input("Would you like to use this story? (y to confirm): ")
    if confirmation.lower() == "y":
        text_adventure.set_story(story)
        ready = True
    
current_location = text_adventure.starting_location
player = {
    "name": "Player",
    "description": "The player character.",
    "stats": {
        "hp": 100,
        "stamina": 100,
        "mana": 100,
        "hunger": 0,
        "thirst": 0,
        "energy": 100
    },
    "special_attributes": {
        "strength": 5,
        "perception": 5,
        "endurance": 5,
        "charisma": 5,
        "intelligence": 5,
        "agility": 5,
        "luck": 5
    },
    "equipment": {
        "headwear": None,
        "upperbodywear": None,
        "gloves": None,
        "lowerbodywear": None,
        "footwear": None,
        "equiped_weapon": None,
        "accessories": [],
    },
    "inventory": []
}

player_name = input("Enter the name of your character: ")
player["name"] = player_name
player_description = input("Enter a description of your character: ")
player["description"] = player_description
for stat in player["special_attributes"]:
    stat_name = stat.upper()[:3]
    if stat_name == "LUC":
        stat_name = "LUK"
    stat_value = input(f"Enter the value for the {stat_name} stat (1-10) (default is 5): ")
    if stat_value.strip() == "":
        stat_value = 5
    try:
        stat_value = int(stat_value)
    except:
        stat_value = 5
        continue
    if stat_value < 1:
        stat_value = 1
    if stat_value > 10:
        stat_value = 10
    player["special_attributes"][stat] = stat_value
    
def print_current_screen():
    description = f"You're currently in {current_location.name}.\n\n{current_location.location_physical_description}\n\n"
    if len(current_location.characters_in_location) > 0:
        # description += "There are people here:\n"
        for character in current_location.characters_in_location:
            if character in text_adventure.met:
                description += f"{character.full_name} is here. {character.get_equipment_description()} "
                if character.stats.hp <= 0:
                    description += f"{character.full_name} is dead."
                description = description.strip()
                description += "\n"
            else:
                description += f"There is {character.get_unknown_description()}. {character.get_equipment_description()} "
                if character.stats.hp <= 0:
                    description += f"{character.get_pronouns()['subject'].capitalize()} is dead."
                description = description.strip()
                description += "\n"
    description = description.strip()
    if len(current_location.objects_in_location) > 0:
        description += "\nItems:\n"
        for item in current_location.objects_in_location:
            position_in_location = item.position_in_location[0].lower() + item.position_in_location[1:]
            if position_in_location[-1] != ".":
                position_in_location += "."
            description += f"There's a \"{item.name}\" {position_in_location}\n"
    description = description.strip()
    if len(current_location.travel_destinations) > 0:
        description += "\n---------------------------------\n"
        description += "Travelable Locations From Here:\n"
        for location in current_location.travel_destinations:
            description += f"\"{location.portal}\" - {location.location_name}\n"
    
    print(description.strip())

print("=====================================")

# clear_console()

first_turn = True
print_current_screen()
while True: # Main game loop
    # Player Turn
    if first_turn:
        action = input("What would you like to do? (type 'help' for a list of commands)> ")
        first_turn = False
    else:
        action = input("> ")
    action_args = action.split(" ")
    if action.lower() == "help" or action.lower() == "h" or action.lower() == "?":
        print("Commands:")
        print("look - Look around the current location.")
        print("travel - Travel to a different location.")
        print("inventory - View your inventory.")
        print("stats - View your stats.")
        print("take - Take an item from the current location.")
        print("drop - Drop an item from your inventory.")
        print("put - Put an item in your inventory.")
        print("equip - Equip an item from your inventory.")
        print("unequip - Unequip an item from your inventory.")
        print("spawn_item - Spawn an item in the current location.")
        print("spawn_character - Spawn a character in the current location.")
        print("say - Say something to a character in the current location.")
        print("eat - Eat food from your inventory.")
        print("attack - Attack a character in the current location.")
        print("help - Display this help message.")
        print("quit - Quit the game.")
    elif action_args[0].lower() == "look" or action_args[0].lower() == "l":
        if len(action_args) > 1:
            at = action.split(" ", 1)[1].strip()
        else:
            at = ""
        if at.lower() == "around":
            at = ""
        if at == "":
            print_current_screen()
        elif at == "me" or at == "myself":
            print(f"{player['name']} - {player['description']}")
            if player["equipment"]["headwear"]:
                print(f"{player['name']} is wearing {player['equipment']['headwear'].physical_description} on their head.")
            if player["equipment"]["upperbodywear"]:
                print(f"{player['name']} is wearing {player['equipment']['upperbodywear'].physical_description} on their upper body.")
            if player["equipment"]["gloves"]:
                print(f"{player['name']} is wearing {player['equipment']['gloves'].physical_description} on their hands.")
            if player["equipment"]["lowerbodywear"]:
                print(f"{player['name']} is wearing {player['equipment']['lowerbodywear'].physical_description} on their lower body.")
            if player["equipment"]["footwear"]:
                print(f"{player['name']} is wearing {player['equipment']['footwear'].physical_description} on their feet.")
            if player["equipment"]["equiped_weapon"]:
                print(f"{player['name']} is holding {player['equipment']['equiped_weapon'].physical_description}.")
        else:
            item_found = False
            for item in current_location.objects_in_location:
                if at.lower() in item.name.lower():
                    print(f"{item.name} - {item.physical_description}")
                    item_found = True
                    break
            if not item_found:
                for character in current_location.characters_in_location:
                    if at.lower() in character.full_name.lower():
                        if character in text_adventure.met:
                            print(f"{character.get_description()}\n{character.get_physical_description()}")
                        else:
                            print(f"There is {character.get_unknown_description()}.\n{character.get_physical_description()}")
                        item_found = True
                        break
                    elif (character not in text_adventure.met and at.lower() in character.get_unknown_description().lower()) or (character in text_adventure.met and at.lower() in character.get_description().lower()) or (at.lower() in character.get_physical_description().lower()):
                        if character in text_adventure.met:
                            print(f"{character.get_description()}\n{character.get_physical_description()}")
                        else:
                            print(f"There is {character.get_unknown_description()}.\n{character.get_physical_description()}")
                        item_found = True
                        break
            if not item_found:
                for item in player["inventory"]:
                    if at.lower() in item.name.lower():
                        print(f"{item.name} - {item.physical_description}")
                        item_found = True
                        break
            if not item_found:
                for item in current_location.objects_in_location:
                    if item.type_string.lower() == "container":
                        for container_item in item.items:
                            if at.lower() in container_item.name.lower() or at.lower() in container_item.physical_description.lower():
                                print(f"{container_item.name} - {container_item.physical_description}")
                                item_found = True
                                break
            if not item_found:
                print(f"Item or character not found in current location: {at}")
    elif action_args[0].lower() == "travel" or action_args[0].lower() == "t" or action_args[0].lower() == "go" or action_args[0].lower() == "walk" or action_args[0].lower() == "move":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify a location to travel to.")
            continue
        travel_to = action_args[1]
        location_found = False
        last_location_name = current_location.name
        for t_location in current_location.travel_destinations:
            if travel_to.lower() in t_location.portal.lower() or travel_to.lower() in t_location.location_name.lower():
                current_location = text_adventure.travel_to_location_from(current_location, t_location)
                location_found = True
                break
        # if not location_found:
        #     for location in text_adventure.locations:
        #         if travel_to.lower() in location.name.lower():
        #             print(f"Location exists, but can't be traveled to from here: {location.name}")
        #             location_found = True
        #             break
        if not location_found:
            print(f"Travelable location not found: {travel_to}\nGenerating new location...")
            travelable_location = text_adventure.generate_travelable_location(current_location, travel_to)
            current_location.travel_destinations.append(travelable_location)
            current_location = text_adventure.travel_to_location_from(current_location, travelable_location)
        if last_location_name != current_location.name:
            print_current_screen()
    elif action.lower() == "inventory" or action.lower() == "i" or action.lower() == "inv":
        print(f"You have {len(player['inventory'])} items in your inventory:")
        for item in player["inventory"]:
            print(f"{item.type_string} - {item.name} - {item.physical_description}")
    elif action.lower() == "stats":
        print("Your stats:")
        print(f"HP: {player['stats']['hp']}")
        print(f"Stamina: {player['stats']['stamina']}")
        print(f"Mana: {player['stats']['mana']}")
        print(f"Hunger: {player['stats']['hunger']}")
        print(f"Thirst: {player['stats']['thirst']}")
        print(f"Energy: {player['stats']['energy']}")
        print("Your SPECIAL stats:")
        for stat in player["special_attributes"]:
            stat_name = stat.upper()[:3]
            if stat_name == "LUC":
                stat_name = "LUK"
            print(f"{stat_name}: {player['special_attributes'][stat]}")
    elif action_args[0].lower() == "take" or action_args[0].lower() == "get" or action_args[0].lower() == "pickup":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to take.")
            continue
        item_to_take = action_args[1]
        item_found = False
        for item in current_location.objects_in_location:
            if item_to_take.lower() in item.name.lower():
                player["inventory"].append(item)
                current_location.objects_in_location.remove(item)
                item_found = True
                print(f"You picked up the {item.name}.")
                break
            elif item.type_string.lower() == "container":
                print(f"Searching {item.name} for {item_to_take}...")
                for container_item in item.items:
                    if item_to_take.lower() in container_item.name.lower() or item_to_take.lower() in container_item.physical_description.lower():
                        player["inventory"].append(container_item)
                        item.items.remove(container_item)
                        for location in text_adventure.locations:
                            if location.name == current_location.name:
                                location.objects_in_location = current_location.objects_in_location
                                break
                        item_found = True
                        print(f"You took the {container_item.name} from the {item.name}.")
        if not item_found:
            for character in current_location.characters_in_location:
                print(f"Searching {character.full_name} for {item_to_take}...")
                if character.equipment.headwear != None:
                    if item_to_take.lower() in character.equipment.headwear.name.lower() or item_to_take.lower() in character.equipment.headwear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            player["inventory"].append(character.equipment.headwear)
                            item_name = character.equipment.headwear.name
                            character.equipment.headwear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.equipment.upperbodywear != None:
                    if item_to_take.lower() in character.equipment.upperbodywear.name.lower() or item_to_take.lower() in character.equipment.upperbodywear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            player["inventory"].append(character.equipment.upperbodywear)
                            item_name = character.equipment.upperbodywear.name
                            character.equipment.upperbodywear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.equipment.gloves != None:
                    if item_to_take.lower() in character.equipment.gloves.name.lower() or item_to_take.lower() in character.equipment.gloves.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            player["inventory"].append(character.equipment.gloves)
                            item_name = character.equipment.gloves.name
                            character.equipment.gloves = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.equipment.lowerbodywear != None:
                    if item_to_take.lower() in character.equipment.lowerbodywear.name.lower() or item_to_take.lower() in character.equipment.lowerbodywear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            player["inventory"].append(character.equipment.lowerbodywear)
                            item_name = character.equipment.lowerbodywear.name
                            character.equipment.lowerbodywear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.equipment.footwear != None:
                    if item_to_take.lower() in character.equipment.footwear.name.lower() or item_to_take.lower() in character.equipment.footwear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            player["inventory"].append(character.equipment.footwear)
                            item_name = character.equipment.footwear.name
                            character.equipment.footwear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.equipment.equiped_weapon != None:
                    if item_to_take.lower() in character.equipment.equiped_weapon.name.lower() or item_to_take.lower() in character.equipment.equiped_weapon.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            player["inventory"].append(character.equipment.equiped_weapon)
                            weapon_name = character.equipment.equiped_weapon
                            character.equipment.equiped_weapon = None
                            print(f"You took the {weapon_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                for item in character.equipment.inventory:
                    if item_to_take.lower() in item.name.lower() or item_to_take.lower() in item.physical_description.lower():
                        if character.stats.hp <= 0:
                            # TODO: Ask the character if they want to give the item to the player
                            player["inventory"].append(item)
                            character.equipment.inventory.remove(item)    
                            item_found = True
                            print(f"You took the {item.name} from {character.full_name}.")
                        else:
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                            item_found = True
                        break
                for item in character.equipment.accessories:
                    if item_to_take.lower() in item.name.lower() or item_to_take.lower() in item.physical_description.lower():
                        if character.stats.hp <= 0:
                            player["inventory"].append(item)
                            character.equipment.accessories.remove(item)
                            item_found = True
                            print(f"You took the {item.name} from {character.full_name}.")
                        else:
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                            item_found = True
                        break
        if not item_found:
            print(f"Item not found: {item_to_take}")
    elif action_args[0].lower() == "drop" or action_args[0].lower() == "discard":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to drop.")
            continue
        item_to_drop = action_args[1]
        item_found = False
        for item in player["inventory"]:
            if item_to_drop.lower() in item.name.lower() or item_to_drop.lower() in item.physical_description.lower():
                current_location.objects_in_location.append(item)
                player["inventory"].remove(item)
                for location in text_adventure.locations:
                    if location.name == current_location.name:
                        location.objects_in_location = current_location.objects_in_location
                        break
                item_found = True
                print(f"You dropped the {item.name}.")
                break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_drop}")
    elif action_args[0].lower() == "put" or action_args[0].lower() == "placein" or action_args[0].lower() == "placeon":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to put.")
            continue
        item_to_put = action_args[1]
        item_found = None
        for item in player["inventory"]:
            if item_to_put.lower() in item.name.lower():
                inventory_found = item
                break
        if inventory_found == None:
            print(f"Item not found in your inventory: {item_to_put}")
            continue
        where_to_put = input("Where would you like to put the item?> ")
        for item in current_location.objects_in_location:
            if where_to_put.lower() in item.name.lower():
                item.items.append(inventory_found)
                player["inventory"].remove(inventory_found)
                for location in text_adventure.locations:
                    if location.name == current_location.name:
                        location.objects_in_location = current_location.objects_in_location
                        break
                item_found = True
                print(f"You put the {inventory_found.name} in the {item.name}.")
                break
    elif action_args[0].lower() == "equip" or action_args[0].lower() == "wear":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to equip.")
            continue
        item_to_equip = action_args[1]
        item_found = False
        for item in player["inventory"]:
            if item_to_equip.lower() in item.name.lower() or item_to_equip.lower() in item.physical_description.lower():
                if item.type_string.lower() == "weapon":
                    player["equipment"]["equiped_weapon"] = item
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "headwear":
                    player["equipment"]["headwear"] = item
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "upperbodywear":
                    player["equipment"]["upperbodywear"] = item
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "lowerbodywear":
                    player["equipment"]["lowerbodywear"] = item
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "footwear":
                    player["equipment"]["footwear"] = item
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "gloves":
                    player["equipment"]["gloves"] = item
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "accessory":
                    player["equipment"]["accessories"].append(item)
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_equip}")
    elif action_args[0].lower() == "unequip" or action_args[0].lower() == "remove":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to unequip.")
            continue
        item_to_unequip = action_args[1]
        item_found = False
        for item in player["equipment"]:
            if item_to_unequip.lower() in item.name.lower() or item_to_unequip.lower() in item.physical_description.lower():
                player["inventory"].append(item)
                player["equipment"].remove(item)
                for location in text_adventure.locations:
                    if location.name == current_location.name:
                        location.objects_in_location = current_location.objects_in_location
                        break
                item_found = True
                print(f"You unequipped the {item.name}.")
                break
        if not item_found:
            print(f"Item not found in your equipment: {item_to_unequip}")
    elif action_args[0].lower() == "spawn_item":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to spawn.")
            continue
        item_to_spawn = action_args[1]
        # item_found = False
        # for item in text_adventure.items:
        #     if item_to_spawn.lower() in item.name.lower() or item_to_spawn.lower() in item.physical_description.lower():
        #         current_location.objects_in_location.append(item)
        #         item_found = True
        #         print(f"You spawned '{item.name}' in the current location.")
        #         break
        # if not item_found:
        # Generate the item
        item = text_adventure.generate_item_from_prompt(item_to_spawn)
        current_location.objects_in_location.append(item)
        item_found = True
        print(f"You spawned '{item.name}' in the current location.")
    elif action_args[0].lower() == "spawn_character":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify a character to spawn.")
            continue
        character_to_spawn = action_args[1]
        # character_found = False
        # for character in text_adventure.characters:
        #     if character_to_spawn.lower() in character.full_name.lower():
        #         current_location.characters_in_location.append(character)
        #         character_found = True
        #         print(f"You spawned '{character.full_name}' in the current location.")
        #         break
        # if not character_found:
        # Generate the character
        character = text_adventure.generate_character_from_prompt(character_to_spawn)
        current_location.characters_in_location.append(character)
        character_found = True
        print(f"You spawned '{character.full_name}' in the current location.")
    elif action_args[0].lower() == "say":
        message = action.split(" ", 1)
        print(f"You say: {message[1]} (This feature is not yet implemented.)")
    elif action_args[0].lower() == "eat" or action_args[0].lower() == "consume":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to eat.")
            continue
        item_to_eat = action_args[1]
        item_found = False
        for item in player["inventory"]:
            if item_to_eat.lower() in item.name.lower() or item_to_eat.lower() in item.physical_description.lower():
                if item.type_string.lower() == "food":
                    player["stats"]["hunger"] += item.hunger_restored
                    player["stats"]["thirst"] += item.thirst_restored
                    player["stats"]["hp"] += item.health_restored
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects_in_location = current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You ate the {item.name}.")
                    break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_eat}")
    elif action_args[0].lower() == "attack" or action_args[0].lower() == "fight" or action_args[0].lower() == "kill" or action_args[0].lower() == "hit" or action_args[0].lower() == "hurt" or action_args[0].lower() == "shoot" or action_args[0].lower() == "punch" or action_args[0].lower() == "stab" or action_args[0].lower() == "slash":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify a character to attack.")
            continue
        character_to_attack = action_args[1]
        character_found = False
        if player["equipment"]["equiped_weapon"] == None:
            print("You need a weapon equipped to attack.")
            continue
        for character in current_location.characters_in_location:
            if character_to_attack.lower() in character.full_name.lower():
                character_found = True
                character.stats.hp -= player["equipment"]["equiped_weapon"].damage
                if character.stats.hp <= 0:
                    print(f"You attacked {character.full_name} with your {player['equipment']['equiped_weapon'].name} and killed them.")
                else:
                    print(f"You attacked {character.full_name} with your {player['equipment']['equiped_weapon'].name}.")
    elif action.lower() == "quit" or action.lower() == "exit" or action.lower() == "q":
        print("Quitting the game...")
        break
    else:
        print("Invalid command. Type 'help' for a list of commands.")
    
    # AI Reaction/AI Turn