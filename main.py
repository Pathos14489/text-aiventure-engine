import json
from openai import OpenAI
import json
from pydantic import BaseModel,Field
from typing import Union
from get_schema_description import get_schema_description, pydantic_to_open_router_schema
import chromadb
from chromadb.config import Settings
import os
from uuid import uuid4
import traceback
import time
from tqdm import tqdm, trange

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

class bcolors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    GREY = '\033[90m'
    BOLD = '\033[1m'
    ITALICS = '\033[3m'
    UNDERLINE = '\033[4m'
    MAGENTA = '\033[35m'
    ENDC = '\033[00m'
    
valid_hex = '0123456789ABCDEF'.__contains__
def cleanhex(data):
    return ''.join(filter(valid_hex, data.upper()))

def fore_fromhex(hexcode):
    """print in a hex defined color"""
    hexint = int(cleanhex(hexcode), 16)
    return f"\x1B[38;2;{hexint>>16};{hexint>>8&0xFF};{hexint&0xFF}m"

def print_colored(text, color:str):
    color = color.upper()
    if color in bcolors.__dict__:
        color_code = getattr(bcolors, color)
        print(f"{color_code}{text}{bcolors.ENDC}")
    else:
        print(text)
    
# CONFIG START
if os.path.exists("config.json"):
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    update_config = False
    if "api_url" in config and config["api_url"] is not None:
        api_url = config["api_url"]
    else:
        api_url = input("Enter the API URL(Default is 'http://localhost:8000/v1/', press Enter to use the default API): ")
        update_config = True
    if "model_name" in config and config["model_name"] is not None:
        model_name = config["model_name"]
    else:
        model_name = input("Enter the model name(Default is 'L3-8B-Stheno-v3.2-Q6_K', press Enter to use the default model): ")
        update_config = True
    if "api_key" in config and config["api_key"] is not None:
        api_key = config["api_key"]
    else:
        api_key = input("Enter the API key(Default is 'abc123', press Enter to use the default key): ")
    if "temp" in config and config["temp"] is not None:
        temp = config["temp"]
    else:
        temp = input("Enter the temperature(Default is 1.12, press Enter to use the default temperature): ")
        if temp == "":
            print_colored("Invalid temperature. Setting to default of 1.12", "RED")
            temp = 1.12
        else:
            try:
                temp = float(temp)
            except ValueError:
                print_colored("Invalid temperature. Setting to default of 1.12", "RED")
                temp = 1.12
        update_config = True
    if "top_p" in config and config["top_p"] is not None:
        top_p = config["top_p"]
    else:
        top_p = input("Enter the top_p(Default is 0.95, press Enter to use the default top_p): ")
        if top_p == "":
            print_colored("Invalid top_p. Setting to default of 0.95", "RED")
            top_p = 0.95
        else:
            try:
                top_p = float(top_p)
            except ValueError:
                print_colored("Invalid top_p. Setting to default of 0.95", "RED")
                top_p = 0.95
        update_config = True
    if "min_p" in config and config["min_p"] is not None:
        min_p = config["min_p"]
    else:
        min_p = input("Enter the min_p(Default is 0.075, press Enter to use the default min_p): ")
        if min_p == "":
            print_colored("Invalid min_p. Setting to default of 0.075", "RED")
            min_p = 0.075
        else:
            try:
                min_p = float(min_p)
            except ValueError:
                print_colored("Invalid min_p. Setting to default of 0.075", "RED")
                min_p = 0.075
        update_config = True
    if "max_tokens" in config and config["max_tokens"] is not None:
        max_tokens = config["max_tokens"]
    else:
        max_tokens = input("Enter the max_tokens(Default is 3072, press Enter to use the default max_tokens): ")
        if max_tokens == "":
            print_colored("Invalid max_tokens. Setting to default of 3072", "RED")
            max_tokens = 3072
        else:
            try:
                max_tokens = int(max_tokens)
            except ValueError:
                print_colored("Invalid max_tokens. Setting to default of 3072", "RED")
                max_tokens = 3072
        update_config = True
    if "openrouter_style_api" in config and config["openrouter_style_api"] is not None:
        openrouter_style_api = config["openrouter_style_api"]
    else:
        openrouter_style_api = input("Are you using an OpenRouter style API? (y/n, default is n): ").lower() == "y"
        update_config = True
else:
    print_colored("Config file not found. Performing first time setup...", "YELLOW")
    api_url = input("Enter the API URL(Default is 'http://localhost:8000/v1/', press Enter to use the default API): ")
    if api_url == "":
        api_url = "http://localhost:8000/v1/"
    model_name = input("Enter the model name(Default is 'L3-8B-Stheno-v3.2-Q6_K', press Enter to use the default model): ")
    if model_name == "":
        model_name = "L3-8B-Stheno-v3.2-Q6_K"
    api_key = input("Enter the API key(Default is 'abc123', press Enter to use the default key): ")
    if api_key == "":
        api_key = "abc123"
    temp = input("Enter the temperature(Default is 1.12, press Enter to use the default temperature): ")
    if temp == "":
        temp = 1.12
    else:
        try:
            temp = float(temp)
        except ValueError:
            print_colored("Invalid temperature. Setting to default of 1.12", "RED")
            temp = 1.12
    top_p = input("Enter the top_p(Default is 0.95, press Enter to use the default top_p): ")
    if top_p == "":
        top_p = 0.95
    else:
        try:
            top_p = float(top_p)
        except ValueError:
            print_colored("Invalid top_p. Setting to default of 0.95", "RED")
            top_p = 0.95
    min_p = input("Enter the min_p(Default is 0.075, press Enter to use the default min_p): ")
    if min_p == "":
        min_p = 0.075
    else:
        try:
            min_p = float(min_p)
        except ValueError:
            print_colored("Invalid min_p. Setting to default of 0.075", "RED")
            min_p = 0.075
    max_tokens = input("Enter the max_tokens(Default is 3072, press Enter to use the default max_tokens): ")
    if max_tokens == "":
        max_tokens = 3072
    else:
        try:
            max_tokens = int(max_tokens)
        except ValueError:
            print_colored("Invalid max_tokens. Setting to default of 3072", "RED")
            max_tokens = 3072
    openrouter_style_api = input("Is this an OpenRouter style API? (y/n, default is n): ").lower() == "y"
    update_config = True
if update_config:
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump({
            "api_url": api_url,
            "model_name": model_name,
            "api_key": api_key,
            "temp": temp,
            "top_p": top_p,
            "min_p": min_p,
            "max_tokens": max_tokens,
            "openrouter_style_api": openrouter_style_api
        }, f, indent=4)

print_colored("Temp: "+str(temp), "green")
print_colored("Top P: "+str(top_p), "green")
print_colored("Min P: "+str(min_p), "green")
print_colored("Max Tokens: "+str(max_tokens), "green")
print_colored("Model Name: "+model_name, "green")
print_colored("API URL: "+api_url, "green")

verbose = False
prototype_ai_turns = True

import argparse
parser = argparse.ArgumentParser(description="Run the prototype AI.")
if __name__ == "__main__":
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--no-prototype-ai-turns", action="store_false", help="Disable prototype AI turns.")
    args = parser.parse_args()
    os.makedirs("saves", exist_ok=True)
    verbose = args.verbose
    prototype_ai_turns = args.no_prototype_ai_turns


# CONFIG END

def generate_id():
    return str(uuid4())

# Schema Patterns

single_sentence = "^[A-Za-z0-9 ]+$"
lower_single_sentence = "^[a-z0-9 ]+$"
hex_pattern = "^([0-9A-Fa-f]{6})$"

# Stats Schemas

class Stats(BaseModel):
    """Stats for a character"""
    hp: int = Field(100, ge=0, description="The character's health points. This is used for things like how much damage the character can take before dying, etc.")
    hunger: int = Field(100, ge=0, le=100, description="The character's hunger level. This is used for things like how hungry the character is, how much they need to eat, etc.")
    thirst: int = Field(100, ge=0, le=100, description="The character's thirst level. This is used for things like how thirsty the character is, how much they need to drink, etc.")
    action_points: int = Field(100, ge=0, description="The character's action points. This is used for things like how many actions the character can take in a turn, etc. Every action and every equipable item takes AP to do.")
    max_action_points: int = Field(100, ge=0, description="The character's action points. This is used for things like how many actions the character can take in a turn, etc. Every action and every equipable item takes AP to do.")

# Item Schemas
class BaseItem(BaseModel):
    """BaseItem Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc. Items can also be food or weapons, which have additional fields. Only Food Items should have a hunger restored and thirst restored value. Only Weapon Items should have a damage value and required SPECIAL stats."""
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

class Item(BaseItem):
    """Item Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc."""
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

class MedicalItem(BaseItem):
    """Medical Item Schema - A medical item in a text adventure game. All fields are required to have a value. Only Medical Items should have a health restored value."""
    type_string: str = Field(description="The type of item.", pattern="^MedicalItem$")
    name: str
    physical_description: str = Field(description="A physical description of the medical item that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a vial with a red cross symbol on it",
        "a bandage with a blue stripe",
        "a bottle of pills with a white label",
        "a syringe with a clear liquid inside",
        "a first aid kit with a green cross symbol",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "In the medicine cabinet",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    health_restored: int = Field(...,ge=0)

class Weapon(BaseItem):
    """Weapon Schema - A weapon item in a text adventure game. Unless a weapon is super complicated, most requirements should be below 5. Anything over 5 for a required SPECIAL stat is considered very high, and should be reserved for very powerful weapons. Only Weapon Items should have a damage value and required SPECIAL stats."""
    type_string: str = Field(description="The type of item.", pattern="^Weapon$")
    name: str
    physical_description: str = Field(description="A physical description of the weapon that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a baseball bat with a wooden handle and a metal barrel",
        "a sword with a sharp blade and a hilt",
        "a gun with a black barrel and a silver trigger",
        "a knife with a serrated edge and a plastic handle",
        "a bow with a wooden frame and a string",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the gun rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    damage: int = Field(...,description="The amount of damage the weapon does. Should be a number between 0 and 100, but can go higher if you want to be extra.")
    strength_required: int = Field(...,description="The amount of strength required to wield the weapon. Should be a number between 1 and 10.")
    perception_required: int = Field(...,description="The amount of perception required to wield the weapon. Should be a number between 1 and 10.")
    endurance_required: int = Field(...,description="The amount of endurance required to wield the weapon. Should be a number between 1 and 10.")
    charisma_required: int = Field(...,description="The amount of charisma required to wield the weapon. Should be a number between 1 and 10.")
    intelligence_required: int = Field(...,description="The amount of intelligence required to wield the weapon. Should be a number between 1 and 10.")
    agility_required: int = Field(...,description="The amount of agility required to wield the weapon. Should be a number between 1 and 10.")
    luck_required: int = Field(...,description="The amount of luck required to wield the weapon. Should be a number between 1 and 10.")

class Chapter(BaseModel):
    """Chapter Schema - A chapter in a book. All fields are required to have a value. Books are composed of chapters. Chapters are at least 5-10 paragraps in chapter_paragraphs length."""
    chapter_title: str = Field(...,description="The title of the chapter. Should be at least a sentence long.", min_length=1)
    chapter_synopsis: str = Field(...,description="A synopsis of the chapter. Should be at least a sentence long.", min_length=1)
    chapter_paragraphs: list[str] = Field(description="The full content of the chapter as a list of paragraphs. Should be at least 5-10 paragraphs long.", min_length=3, max_length=5)

class Book(BaseItem):
    """Book Schema - A book item in a text adventure game. All fields are required to have a value. Books are short stories comprised of chapters. Chapters are at least 5-10 paragraphs in chapter length. The chapters should tell a complete story/account of the topic of the book by the final chapter. Every chapter should have a distinct start and end that follows the plot of the book in question and tells the complete story of the chapter synopsis. There are no content restrictions on the content of a book."""
    type_string: str = Field(description="The type of item.", pattern="^Book$")
    name: str
    physical_description: str = Field(description="A physical description of the book that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a dark blue book with a golden spine and a red cover",
        "a thick book with a black cover and a white spine",
        "a small book with a green cover and a yellow spine",
        "a paperback book with a blue cover and a red spine",
        "a hardcover book with a black cover and a white spine",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the bookshelf",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)
    # page_count: int = Field(...,ge=0)
    genre: str = Field(...,description="The genre of the book.")
    book_synopsis: str = Field(...,description="A synopsis of the book. Should be at least a sentence long.", min_length=1)
    chapters: list[Chapter] = Field(description="A list of chapters in the book. Each chapter should have a title and a synopsis. Chapters can be used to group items, characters, or locations together. Chapters can also be used to store the state of the game. Chapters can be used to store the state of the game, and can be used to save and load the game. Books should have 5-10 chapters, and each chapter should be 5-10 paragraphs long.",max_length=10, min_length=5)

# Clothing Schemas
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

class Gloves(BaseItem):
    """Gloves Schema - A gloves item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^Gloves$")
    name: str
    physical_description: str = Field(description="A physical description of the gloves that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a pair of black leather gloves with a soft lining and a snug fit",
        "a pair of red knitted gloves with a warm and cozy feel",
        "a pair of blue rubber gloves with a textured grip and a long cuff",
        "a pair of green gardening gloves with a breathable fabric and reinforced fingertips",
        "a pair of white cotton gloves with a delicate lace trim and a comfortable fit",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the glove rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)

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

class UpperbodyUnderwear(BaseItem):
    """Underwear Schema - An underwear item in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of item.", pattern="^UpperbodyUnderwear$")
    name: str = Field(description="The name of the underwear.", examples=[
        "Bra",
        "Panties",
        "Red Bikini Top",
        "Sports Bra"
    ])
    physical_description: str = Field(description="A physical description of the underwear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a bra with a floral pattern and lace trim",
        "a bikini top with a bright red color and a halter neck",
        "a sports bra with a comfortable fit and moisture-wicking fabric",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the underwear rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)

class BottomUnderwear(BaseItem):
    """Lower Underwear Schema - An underwear item in a text adventure game. All fields are required to have a value. Underwear can also be a swimsuit, or other undergarments."""
    type_string: str = Field(description="The type of item.", pattern="^BottomUnderwear$")
    name: str = Field(description="The name of the underwear.", examples=[
        "Boxers",
        "Briefs",
        "Red Bikini Bottom",
        "Thong"
    ])
    physical_description: str = Field(description="A physical description of the underwear that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a pair of black lace panties with a floral pattern",
        "a red bikini bottom with a high-cut leg and a comfortable fit",
        "a pair of blue boxer shorts with a fun print and an elastic waistband",
    ], pattern=lower_single_sentence)
    position_in_location: str = Field(description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the underwear rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ], pattern=lower_single_sentence)

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

# Complex Item Schemas
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
    items: list[Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory]]    
    value: int = Field(...,ge=0)
    weight: int = Field(...,ge=0)


# Generic Item Schema
class SomeItem(BaseModel):
    """SomeItem Schema - Any item in a text adventure game. All fields are required to have a value."""
    item: Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory,MedicalItem,Container,Book]

# Character Schemas

class SPECIALAttributes(BaseModel):
    """SPECIAL Stats for a character, 1-10"""
    strength: int = Field(ge=0)
    perception: int = Field(ge=0)
    endurance: int = Field(ge=0)
    charisma: int = Field(ge=0)
    intelligence: int = Field(ge=0)
    agility: int = Field(ge=0)
    luck: int = Field(ge=0)

class WornClothing(BaseModel):
    """WornClothing Schema - The clothes that a character has on them. This includes all worn clothing, armour and accessories. If the character has no equipment on them, this property should be null."""
    headwear: Union[Headwear,None] = Field(description="The headwear that the character has equiped. If the character has no headwear equiped, this property should be null.")
    fullbodywear: Union[FullBodywear,None] = Field(description="The fullbodywear that the character has equiped. This is only for outfits that cover the entire body. A dress, a jumpsuit, a suit, etc. If the character has no fullbodywear equiped, this property should be null. Multiple clothing items can be used to cover the entire body, so this is not required to be a full outfit. If the character has no fullbodywear equiped, this property should be null.")
    upperbodywear: Union[UpperBodywear,None] = Field(description="The upperbodywear that the character has equiped. If the character has no upperbodywear equiped, this property should be null.")
    upperbody_underwear: Union[UpperbodyUnderwear,None] = Field(description="The underwear that the character has equiped on their upperbody. If the character has no underwear equiped, this property should be null.")
    gloves: Union[Gloves,None] = Field(description="The gloves that the character has equiped. If the character has no gloves equiped, this property should be null.")
    bottom_underwear: Union[BottomUnderwear,None] = Field(description="The underwear that the character has equiped. If the character has no underwear equiped, this property should be null.")
    lowerbodywear: Union[LowerBodywear,None] = Field(description="The lowerbodywear that the character has equiped. If the character has no lowerbodywear equiped, this property should be null.")
    footwear: Union[Footwear,None] = Field(description="The footwear that the character has equiped. If the character has no footwear equiped, (e.g. they are bare foot), this property should be null.")
    accessories: list[Accessory] = Field(description="A list of accessories that the character has on them. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required SPECIAL stats. If an item is a weapon, it MUST have a damage value and required SPECIAL stats. If an item is food, it MUST have a hunger restored and thirst restored value. This is not worn equipment, but items that the character has in their inventory.")

class BodyPartDescriptions(BaseModel):
    """Body Part Descriptions Schema - A set of descriptions for a character's body parts. Should not describe their clothes or equipment in any way. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that they should cohesively flow together, seperated by new lines, and not repeat themselves. All fields are required to have a value. Body part descriptions should only use the characters gender to refer to them, never by name. Example: \"She has a cute face.\" Additionally, NEVER mention what the NPC is wearing when describing their body parts. All clothing MUST be an WornClothing item."""
    hair_description: str = Field(...,description="A description of the character's hair. Should be at least a paragraph long and explicitly and graphically describe the character's hair.", min_length=1, examples=[
        "She has long, flowing, blonde hair that cascades down her back in gentle waves."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    face_description: str = Field(...,description="A description of the character's face. Should be at least a paragraph long and explicitly and graphically describe the character's nude face.", min_length=1, examples=[
        "She has a cute face with big, bright eyes and a small, upturned nose."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    naked_bare_chest_descriptioniption: str = Field(...,description="A description of the character's chest without clothes. Should be at least a paragraph long and explicitly and graphically describe the character's nude chest.", min_length=1, examples=[
        "She has a perky pair of breasts with small, pink nipples that stand out against her pale skin."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    abdomen_description: str = Field(...,description="A description of the character's abdomen not including the chest or genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude body.", min_length=1, examples=[
        "Her abdomen is flat and toned, with a small belly button in the center."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    naked_genital_description: str = Field(...,description="A description of the character's genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude genitals.", min_length=1, examples=[
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
    """Character Schema - No stats, just descriptions. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Personality, Appearance, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Drives are what motivates the character, and can be things like "Revenge on the bandits who killed their family" or "To find the lost city of gold". Tags are used to help search for characters, and can be things like "Elf", "Wizard", "Pirate", etc. The voice description is seperate from the other descriptions, and should be able to exist by itself without the other descriptions. It should describe how the character should sound. All descriptions should be at least a paragraph long, and the first message should be at least a sentence long, but longer is not bad. The backstory is the character's history, and should be at least a paragraph long. The naked body description is what the character looks like without clothes, and should be at least a paragraph long and explicitly and graphically describe the character's nude body. All fields are required to have a value. Make sure characters are wearing adequate clothing for the scenario requested(or lack of clothing if it's necessary). Example: If someone is from the middle ages, they should be wearing era appropriate equipemnt!"""
    full_name: str = Field(..., min_length=1) # Tricks the LLM into prompting itself to generate a name
    nick_name: str = Field(..., min_length=1)
    age: int = Field(...)
    gender: str = Field(...,examples=["Male","Female"],pattern="^(Male|Female)$")
    race: str
    racial_gender_term: str = Field(...,examples=["Man", "Boy", "Woman", "Girl"], description="The gender term specific to this character. For example, an adult human male would be 'man', a child male would be a 'boy', etc.")
    species: str
    special_attributes: SPECIALAttributes
    stats: Stats = Field(None,description="The character's stats. This is used for things like how much damage the character can take before dying, etc.")
    clothing_prompt: str = Field(...,description="A description of the character's clothing. Should be at least a sentence long.", min_length=1) # Tricks the LLM into prompting itself to generate clothing
    worn_clothing: WornClothing = Field(...,description="The character's clothing that they're wearing or not wearing. This is used for things like what the character is wearing, what weapons they have, etc.")
    equiped_weapon: Union[Weapon,None] = Field(description="The weapon that the character has equiped. If the character has no weapon equiped, this property should be null.")
    inventory: list[Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory]] = Field(description="A list of objects that the character has on them. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required SPECIAL stats. If an item is a weapon, it MUST have a damage value and required SPECIAL stats. If an item is food, it MUST have a hunger restored and thirst restored value. This is not worn equipment, but items that the character has in their inventory. To be in a characters inventory, they must be actively carrying the item. Items in the inventory are not equiped, and are not being worn by the character. They CANNOT be on the ground, in a box, on a table, etc. They MUST be in the character's possession on their person.")
    hex_color: str = Field(...,description="The hex color code for the character's name. Should be a 6 character hex code, without the #.",pattern=hex_pattern)
    personality_description: str
    naked_body_part_descriptions: BodyPartDescriptions
    backstory: str = Field(...,description="A description of the character's backstory. Should be at least a paragraph long.", min_length=1)
    processing: bool = True
    id: str = Field(default_factory=generate_id)

    def __init__(self, **data):
        super().__init__(**data)
        self.stats = Stats(hp=100,hunger=100,thirst=100)
        self.processing = True

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
        return f"{self.full_name.strip()} is a {str(self.age).strip()} year old {self.racial_gender_term.lower()}. {self.get_pronouns()['subject'].capitalize()} is a {bcolors.BLUE}{self.race.strip()} {self.species.strip()}{bcolors.ENDC}. {self.personality_description.strip()} {self.backstory.strip()}"
    
    def get_unknown_description(self, capitalize=False):
        if capitalize:
            description = f"{bcolors.GREY}A"
        else:
            description = f"{bcolors.GREY}a"
        if self.race.lower().strip() != "":
            if self.race.lower()[0] in "aeiou":
                description += "n"
            description += f" {bcolors.ENDC}{bcolors.BLUE}{self.race.lower().strip()}{bcolors.ENDC}{bcolors.GREY}"
        if self.species.lower().strip() != "" and self.race.lower() != self.species.lower():
            description += f" {self.species.lower().strip()}"
        if self.racial_gender_term.lower().strip() != "" and self.race.lower() != self.species.lower() and self.racial_gender_term.lower() != self.species.lower() and self.racial_gender_term.lower() != self.race.lower():
            description += f" {self.racial_gender_term.lower().strip()}"
        return f"{description.strip()}{bcolors.ENDC}".strip()
    
    def get_physical_description(self):
        # return physical appearance accounting for equipment
        description = ""
        if self.worn_clothing.headwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.headwear.physical_description}.\n"
            if not self.worn_clothing.headwear.covers_hair:
                description += f"{self.naked_body_part_descriptions.hair_description}.\n"
            if not self.worn_clothing.headwear.covers_face:
                description += f"{self.naked_body_part_descriptions.face_description}.\n"
        else:
            description += f"{self.naked_body_part_descriptions.hair_description}.\n"
            description += f"{self.naked_body_part_descriptions.face_description}.\n"
        if self.worn_clothing.upperbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.upperbodywear.physical_description[0].lower()}{self.worn_clothing.upperbodywear.physical_description[1:]}.\n"
            if not self.worn_clothing.upperbodywear.covers_breasts and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_breasts) and not self.worn_clothing.upperbody_underwear:
                description += f"{self.naked_body_part_descriptions.naked_bare_chest_descriptioniption}.\n"
            if not self.worn_clothing.upperbodywear.covers_belly and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_belly):
                description += f"{self.naked_body_part_descriptions.abdomen_description}.\n"
        else:
            if self.worn_clothing.fullbodywear:
                description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.fullbodywear.physical_description[0].lower()}{self.worn_clothing.fullbodywear.physical_description[1:]}.\n"
                if not self.worn_clothing.fullbodywear.covers_breasts:
                    description += f"{self.naked_body_part_descriptions.naked_bare_chest_descriptioniption}.\n"
                if not self.worn_clothing.fullbodywear.covers_belly:
                    description += f"{self.naked_body_part_descriptions.abdomen_description}.\n"
            else:
                if self.worn_clothing.upperbody_underwear:
                    description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.upperbody_underwear.physical_description[0].lower()}{self.worn_clothing.upperbody_underwear.physical_description[1:]}.\n"
                else:
                    description += f"{self.naked_body_part_descriptions.naked_bare_chest_descriptioniption}.\n"
                description += f"{self.naked_body_part_descriptions.abdomen_description}.\n"
        if self.worn_clothing.gloves:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.gloves.physical_description[0].lower()}{self.worn_clothing.gloves.physical_description[1:]}.\n"
        else:
            description += f"{self.naked_body_part_descriptions.hands_description}.\n"
        if self.worn_clothing.lowerbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.lowerbodywear.physical_description[0].lower()}{self.worn_clothing.lowerbodywear.physical_description[1:]}.\n"
            if not self.worn_clothing.lowerbodywear.covers_legs and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_legs):
                description += f"{self.naked_body_part_descriptions.legs_description}.\n"
            if not self.worn_clothing.lowerbodywear.covers_genitals and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_genitals) and not self.worn_clothing.bottom_underwear:
                description += f"{self.naked_body_part_descriptions.naked_genital_description}.\n"
            if not self.worn_clothing.lowerbodywear.covers_butt and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_butt):
                description += f"{self.naked_body_part_descriptions.butt_description}.\n"
        else:
            if self.worn_clothing.fullbodywear:
                if not self.worn_clothing.fullbodywear.covers_legs:
                    description += f"{self.naked_body_part_descriptions.legs_description}.\n"
                if not self.worn_clothing.fullbodywear.covers_genitals:
                    if not self.worn_clothing.bottom_underwear:
                        description += f"{self.naked_body_part_descriptions.naked_genital_description}.\n"
                    else:
                        description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.bottom_underwear.physical_description[0].lower()}{self.worn_clothing.bottom_underwear.physical_description[1:]}.\n"
                else:
                    description += f"{self.naked_body_part_descriptions.legs_description}.\n"
                if not self.worn_clothing.fullbodywear.covers_butt and not self.worn_clothing.bottom_underwear:
                    description += f"{self.naked_body_part_descriptions.butt_description}.\n"
                else:
                    description += f"{self.naked_body_part_descriptions.butt_description}.\n"
            else:
                if not self.worn_clothing.bottom_underwear:
                    description += f"{self.naked_body_part_descriptions.naked_genital_description}.\n"
                else:
                    description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.bottom_underwear.physical_description[0].lower()}{self.worn_clothing.bottom_underwear.physical_description[1:]}.\n"
        if self.worn_clothing.footwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.footwear.physical_description[0].lower()}{self.worn_clothing.footwear.physical_description[1:]}.\n"
        else:
            description += f"{self.naked_body_part_descriptions.feet_description}\n"
        if self.stats.hp <= 0:
            description += f"{self.get_pronouns()['subject'].capitalize()} is dead."
            if self.equiped_weapon:
                description += f"{self.get_pronouns()['object'].capitalize()} weapon, a {self.equiped_weapon.physical_description}, is lying on the ground beside {self.get_pronouns()['object']} body."
        else:
            if self.equiped_weapon:
                description += f"{self.get_pronouns()['subject'].capitalize()} is holding {self.equiped_weapon.physical_description}."
        description.replace("...","[ellipsis]")
        while ".." in description:
            description = description.replace("..",".")
        description = description.replace("[ellipsis]","...")
        while "!." in description:
            description = description.replace("!.","!")
        while "?." in description:
            description = description.replace("?.","?")
        return description.strip()

    def get_equipment_description(self):
        # return equipment description
        description = ""
        if self.worn_clothing.headwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.headwear.physical_description[0].lower()}{self.worn_clothing.headwear.physical_description[1:]}. "
        if self.worn_clothing.fullbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.fullbodywear.physical_description[0].lower()}{self.worn_clothing.fullbodywear.physical_description[1:]}. "
        if self.worn_clothing.upperbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.upperbodywear.physical_description[0].lower()}{self.worn_clothing.upperbodywear.physical_description[1:]}. "
        if self.worn_clothing.gloves:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.gloves.physical_description[0].lower()}{self.worn_clothing.gloves.physical_description[1:]}. "
        if self.worn_clothing.lowerbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.lowerbodywear.physical_description[0].lower()}{self.worn_clothing.lowerbodywear.physical_description[1:]}. "
        if self.worn_clothing.footwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.footwear.physical_description[0].lower()}{self.worn_clothing.footwear.physical_description[1:]}. "
        if self.equiped_weapon:
            description += f"{self.get_pronouns()['subject'].capitalize()} is holding {self.equiped_weapon.physical_description[0].lower()}{self.equiped_weapon.physical_description[1:]}. "
        description = description.strip()
        if description == "":
            description = f"{self.get_pronouns()['subject'].capitalize()} is completely naked."
        description.replace("...","[ellipsis]")
        while ".." in description:
            description = description.replace("..",".")
        description = description.replace("[ellipsis]","...")
        while "!." in description:
            description = description.replace("!.","!")
        while "?." in description:
            description = description.replace("?.","?")
        return description
    
    def get_inventory_description(self):
        # return inventory description
        description = ""
        if len(self.inventory) == 0:
            description = f"{self.get_pronouns()['subject'].capitalize()} has nothing in {self.get_pronouns()['object']} inventory."
        else:
            description = f"{self.get_pronouns()['subject'].capitalize()} has the following items in {self.get_pronouns()['object']} inventory:\n"
            for item in self.inventory:
                description += f"- {item.physical_description}\n"
        description.replace("...","[ellipsis]")
        while ".." in description:
            description = description.replace("..",".")
        description = description.replace("[ellipsis]","...")
        while "!." in description:
            description = description.replace("!.","!")
        while "?." in description:
            description = description.replace("?.","?")
        return description.strip()

# Location Schemas - The rooms in the text adventure game
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
    location_physical_description: str = Field(description="A brief description of the location. Can be a city, a forest, a mountain, a cave, etc. The description of the location.", examples=[
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

class Location(BaseModel):
    """Location Schema - A location in a text adventure game. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that they are all separate sections that should cohesively flow together, seperated by new lines, and not repeat themselves. Tags are used to help search for locations, and can be things like "Forest", "Castle", "Desert", etc. All fields are required to have a value."""
    id: str = Field(default_factory=generate_id)
    name: str = Field(description="The name of the location.", min_length=1, examples=[
        "The Dark Cave",
        "The Enchanted Forest",
        "The Haunted Mansion",
        "The Abandoned Town",
        "The Deserted Island",
        "The Lost City"
    ])
    location_physical_description: str = Field(description="A description of the location. Should be at least a paragraph long. MUST NOT contain any information about items or characters in the location. This should strictly be a description of the location without any storytelling involved. No talking about how the player moves, don't include plot elements or thoughts that the player is thinking, merely describe the location as detailedly as possible. This should NOT describe the items or characters in the location, only the physical description of the location itself. If the user's prompt includes objects or characters in the location, they should be described in the objects_in_location and npcs_in_location fields ONLY.", min_length=1, examples=[
        "A dark, damp cave with a low ceiling and a musty smell.",
        "A dense, overgrown forest with tall trees and thick underbrush.",
        "A large, spooky mansion with creaky floors and drafty hallways.",
        "An old, abandoned town with crumbling buildings and overgrown streets.",
        "A small, sandy island with palm trees and crystal clear water.",
        "A ruined city with crumbling buildings and twisted metal."
    ])
    travel_destinations: list[TravelableLocation] = Field(description="A list of locations that can be traveled to from this location. Each travelable location should have a portal, location name, and location prompt. All possible travelable locations from this location. If this is in a section of a town for instance, it could have a travelable location to the market, the inn, the blacksmith, travelable locations out of town, travelable locations to the other parts of town, etc. Be detailed when coming up with travelable locations. Travel locations should usually be logical and reasonable. For example, if you're lost in a white void with just a cake, you could do \"Explore the void\" but wouldn't do \"The Cake\" unless the cake was large enough to stand on.", min_length=1)
    objects_in_location: list[Union[Item,Food,Weapon,Headwear,Footwear,Gloves,LowerBodywear,UpperBodywear,Accessory,MedicalItem,Container,Book]] = Field(description="A list of objects in the location. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required SPECIAL stats. If an item is a weapon, it MUST have a damage value and required SPECIAL stats. If an item is food, it MUST have a hunger restored and thirst restored value.")
    npcs_in_location: list[Character] = Field(description="A list of characters in the location.")

# Story Schema

class Story(BaseModel):
    """Story Schema - A story in a text adventure game. Summarizes the vibe and aesthetic of the story. All fields are required to have a value. Player character should not be included in starting_location's NPCs."""
    # title: str
    # setting: str = Field(description="The setting of the story. Can be a city, a forest, a mountain, a cave, etc.")
    id: str = Field(default_factory=generate_id)
    vibe: str = Field(description="The vibe of the story.")
    aesthetic: str = Field(description="The aesthetic of the story. Can be a genre, a theme, a style, etc. The overall feel of the story and the writing of the items, characters, and locations.")
    starting_location: Location = Field(description="The starting location of the story.")

# NPC Decision Schemas

class SayDecision(BaseModel):
    """Say Decision Schema - A decision made by an NPC to say smoething in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Say$")
    message: str = Field(description="The message that the NPC wants to say.", min_length=1)

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Say",
            "message": "Hello, how are you?"
        }

class ActionDecision(BaseModel):
    """Action Decision Schema - A decision made by an NPC to roleplay an arbitrary action in the text adventure game. All fields are required to have a value. Roleplaying arbitrary actions has no effect on the state of the game world, the objects in it, or the NPCs within it, and is purely for aesthetic."""
    type_string: str = Field(description="The type of decision.", pattern="^Action$")
    message: str = Field(description="The message that the NPC wants to say.", min_length=1, examples=[
        "opens the door",
        "shakes their head",
        "sighs",
        "nods",
        "smiles and gives David a hug",
    ], pattern="^[a-z]([A-Za-z0-9 ])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Action",
            "message": "opens the door"
        }

class TakeDecision(BaseModel):
    """Take Decision Schema - A decision made by an NPC to pick up an item in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Take$")
    item: str = Field(description="The item that the NPC wants to pick up.", min_length=1, pattern="^([a-z0-9-])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Take",
            "item": "The Sword of Destiny"
        }

class DropDecision(BaseModel):
    """Drop Decision Schema - A decision made by an NPC to drop an item in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Drop$")
    item: str = Field(description="The item that the NPC wants to drop.", min_length=1, pattern="^([a-z0-9-])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Drop",
            "item": "The Sword of Destiny"
        }

class AttackDecision(BaseModel):
    """Attack Decision Schema - A decision made by an NPC to attack another NPC in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Attack$")
    target: str = Field(description="The target that the NPC wants to attack.", min_length=1, pattern="^([a-z0-9-])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Attack",
            "target": "The Dragon"
        }

class EquipDecision(BaseModel):
    """Equip Decision Schema - A decision made by an NPC to equip an item in the text adventure game. This must be used to put on clothes and to equip weapons. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Equip$")
    item: str = Field(description="The item that the NPC wants to equip. This should be a simple noun from the name of the item.", min_length=1, pattern="^([a-z0-9-])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Equip",
            "item": "The Sword of Destiny"
        }

class UnequipDecision(BaseModel):
    """Unequip Decision Schema - A decision made by an NPC to unequip an item in the text adventure game. This must be used to remove all clothes and to unequip weapons. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Unequip$")
    item: str = Field(description="The item that the NPC wants to unequip. This should be a simple noun from the name of the item.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)

    @staticmethod
    def model_example():
        return {
            "type_string": "Unequip",
            "item": "The Sword of Destiny"
        }




# Game Master Decision Schemas

class TeleportDecision(BaseModel):
    """Teleport Decision Schema - A decision made by the game master to teleport a character to a new location in the text adventure game. Teleports don't leave a path between where they were and where they went. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Teleport$")
    character: str = Field(description="The full name of the character that the game master wants to teleport.", min_length=1, pattern="^([a-z0-9- ])*$")
    location: str = Field(description="The location that the game master wants to teleport the character to.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Teleport",
            "character": "John Doe",
            "location": "The Dark Cave"
        }

class SpawnCharacterDecision(BaseModel):
    """Spawn Character Decision Schema - A decision made by the game master to spawn a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^CharacterSpawn$")
    prompt: str = Field(description="The prompt that the game master wants to use to spawn the character.", min_length=1, pattern="^([a-z0-9- ])*$", examples=[
        "A brave knight.",
        "A cunning thief.",
        "A wise wizard.",
        "A fierce warrior.",
        "A skilled archer."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "CharacterSpawn",
            "prompt": "A brave knight."
        }

class SpawnItemDecision(BaseModel):
    """Spawn Item Decision Schema - A decision made by the game master to spawn an item in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^ItemSpawn$")
    prompt: str = Field(description="The prompt that the game master wants to use to spawn the item.", min_length=1, pattern="^([a-z0-9- ])*$", examples=[
        "A shiny sword.",
        "A rusty dagger.",
        "A magical staff.",
        "A healing potion.",
        "A mysterious amulet."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "ItemSpawn",
            "prompt": "A shiny sword."
        }

class SpawnNewLocationDecision(BaseModel):
    """Spawn New Location Decision Schema - A decision made by the game master to spawn a new location in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^NewLocationSpawn$")
    prompt: str = Field(description="The prompt that the game master wants to use to spawn the new location.", min_length=1, pattern="^([a-z0-9- ])*$", examples=[
        "A hidden cave entrance under the waterfall.",
        "A secret passage behind a bookshelf that leads to a hidden room.",
        "A hidden door to the outside.",
        "A trapdoor in the floor.",
        "A secret tunnel leading to the end of the dungeon."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "NewLocationSpawn",
            "prompt": "A hidden cave entrance under the waterfall."
        }

class FurtherDescribeCurrentLocationDecision(BaseModel):
    """Further Describe Current Location Decision Schema - A decision made by the game master to modify the physical description of the current location in the text adventure game. This should only be used to further describe more details about the current location, not the actions of the players or NPCs in the location. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^ModifyLocationDescription$")
    description_addition: str = Field(description="The description that the game master wants to add to the current location.", min_length=1, pattern="^[A-Z]([a-z0-9- ])*$", examples=[
        "As you look closer, you see a small glimmer of light in the distance.",
        "You hear a faint rustling sound coming from the bushes.",
        "A strange smell fills the air, like something rotting.",
        "You notice a small crack in the wall that wasn't there before.",
        "A shadow flits past your vision, but when you turn to look, there's nothing there."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "ModifyLocationDescription",
            "description_addition": "As you look closer, you see a small glimmer of light in the distance."
        }

class GivePlayerItemDecision(BaseModel):
    """Give Player Item Decision Schema - A decision made by the game master to give the player an item in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^GivePlayerItem$")
    item: str = Field(description="The item that the game master wants to give to the player.", min_length=1, pattern="^([a-z0-9- ])*$", examples=[
        "A shiny sword.",
        "A rusty dagger.",""
        "A magical staff.",
        "A healing potion.",
        "A mysterious amulet."
    ])

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "GivePlayerItem",
            "item": "A shiny sword."
        }

class DamageDecision(BaseModel):
    """Damage Decision Schema - A decision made by the game master to damage a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Damage$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to damage.", min_length=1, pattern="^([a-z0-9- ])*$")
    damage: int = Field(description="The amount of damage that the game master wants to deal to the character.", ge=1)

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Damage",
            "target_character_name": "John Doe",
            "damage": 10
        }

class KillDecision(BaseModel):
    """Kill Decision Schema - A decision made by the game master to kill a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Kill$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to kill.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Kill",
            "target_character_name": "John Doe"
        }
        
class EquipItemDecision(BaseModel):
    """Equip Item Decision Schema - A decision made by the game master to equip an item to a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Equip$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to equip the item to.", min_length=1, pattern="^([a-z0-9- ])*$")
    item: str = Field(description="The name of the item that the game master wants to equip to the character.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Equip",
            "target_character_name": "John Doe",
            "item": "The Sword of Destiny"
        }

class UnequipItemDecision(BaseModel):
    """Unequip Item Decision Schema - A decision made by the game master to unequip an item from a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Unequip$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to unequip the item from.", min_length=1, pattern="^([a-z0-9- ])*$")
    item: str = Field(description="The name of the item that the game master wants to unequip from the character.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Unequip",
            "target_character_name": "John Doe",
            "item": "The Sword of Destiny"
        }

class DropItemDecision(BaseModel):
    """Drop Item Decision Schema - A decision made by the game master to drop an item from a character in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^Drop$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to drop the item from.", min_length=1, pattern="^([a-z0-9- ])*$")
    item: str = Field(description="The name of the item that the game master wants to drop from the character.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "Drop",
            "target_character_name": "John Doe",
            "item": "The Sword of Destiny"
        }

class PickUpItemDecision(BaseModel):
    """Pick Up Item Decision Schema - A decision made by the game master to pick up an item from a location in the text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of decision.", pattern="^PickUp$")
    target_character_name: str = Field(description="The full name of the character that the game master wants to pick up the item for.", min_length=1, pattern="^([a-z0-9- ])*$")
    item: str = Field(description="The name of the item that the game master wants to pick up from the location.", min_length=1, pattern="^([a-z0-9- ])*$")

    def __init__(self, **data):
        super().__init__(**data)
    @staticmethod
    def model_example():
        return {
            "type_string": "PickUp",
            "target_character_name": "John Doe",
            "item": "The Sword of Destiny"
        }

# Generic Character Card

# JSON Schema
# {
#     "name": "Name",
#     "description": "",
#     "personality": "",
#     "first_mes": "",
#     "avatar": "https://avatars.charhub.io/avatars/abc123/name-id/chara_card_v2.png",
#     "mes_example": "",
#     "scenario": "",
#     "creator_notes": "",
#     "system_prompt": "",
#     "post_history_instructions": "",
#     "alternate_greetings": [],
#     "tags": [],
#     "creator": "abc123",
#     "character_version": "main",
#     "character_book": null
# }

class CharacterCard(BaseModel):
    """Character Card Schema - A character card in a text adventure game. All fields are required to have a value."""
    name: str = Field(description="The name of the character.")
    description: str = Field(description="A description of the character.")
    personality: str = Field(description="The personality of the character.")
    first_mes: str = Field(description="The first message of the character.")
    avatar: str = Field(description="The avatar of the character.")
    mes_example: str = Field(description="An example message from the character.")
    scenario: str = Field(description="The scenario of the character.")
    creator_notes: str = Field(description="Notes from the creator of the character.")
    system_prompt: str = Field(description="The system prompt for the character.")
    post_history_instructions: str = Field(description="Instructions for the character after history is loaded.")
    alternate_greetings: list[str] = Field(description="Alternate greetings for the character.")
    tags: list[str] = Field(description="Tags for the character.")
    creator: str = Field(description="The creator of the character.")
    character_version: str = Field(description="The version of the character.")
    character_book: Union[dict,list,None] = Field(description="The book that the character is from.")

# General Schemas

class Character_Prompt(BaseModel):
    """Character Prompt Schema - A prompt for a character in a text adventure game. All fields are required to have a value."""
    prompt_type: str = Field(description="The type of prompt.", pattern="^Character$")
    prompt: str = Field(description="The prompt for the character.", min_length=1, examples=[
        "A brave knight.",
        "A cunning thief.",
        "A wise wizard.",
        "A fierce warrior.",
        "A skilled archer."
    ], pattern="^[A-Za-z0-9 ]*$")

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

class TravelableLocation_Prompt(BaseModel):
    """Travelable Location Prompt Schema - A prompt for a travelable location in a text adventure game. All fields are required to have a value."""
    prompt_type: str = Field(description="The type of prompt.", pattern="^TravelableLocation$")
    prompt: str = Field(description="The prompt for the travelable location.", min_length=1, examples=[
        "A hidden cave entrance under the waterfall.",
        "A secret passage behind a bookshelf that leads to a hidden room.",
        "A hidden door to the outside.",
        "A trapdoor in the floor.",
        "A secret tunnel leading to the end of the dungeon."
    ], pattern="^[A-Za-z0-9 ]*$")

class Prompts(BaseModel):
    """Prompts Schema - A list of prompts for a text adventure game. All fields are required to have a value. The prompts should be a list of 'Character', 'Item', and 'TravelableLocation' prompts. The prompts will be used to generate the characters, items, and travelable locations in the text adventure game. All fields are required to have a value."""
    prompts: list[Union[Character_Prompt,Item_Prompt,TravelableLocation_Prompt]] = Field(description="A list of prompts for the text adventure game. Each prompt should have a type and a prompt. All prompts for the text adventure game.", min_length=1)
    

# Text Adventure Engine

class TextAIventureEngine():
    def __init__(self):
        self.story_id:str = None
        self.story_vibe:str = None
        self.story_aesthetic:str = None
        self.starting_location:Location = None
        self.current_location:Location = None
        self.locations: list[Location] = []
        self.characters: list[Character] = []
        self.met: list[Character] = []
        self.travel_order: list[Location] = [] # list of the last 5 locations visited
        self.client = OpenAI(api_key=api_key, base_url=api_url)
        self.chroma_path = f"./chromadb"
        self.chroma_client = chromadb.PersistentClient(self.chroma_path,Settings(anonymized_telemetry=False))
        self.temp = 1.12
        self.top_p = 0.96
        self.min_p = 0.075
        self.max_tokens = 3.5*1024
        self.verbose = verbose
        self.travel_order_length = 10
        self.messages_db = self.chroma_client.get_or_create_collection("messages")
        self.player: Union[Character,None] = None

    def generate_story(self, prompt:str):
        if self.verbose:
            # print("Generating Story Starter for Prompt:",prompt)
            print_colored("Generating Story Starter for Prompt: "+prompt, color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a story JSON to run the text adventure game with. It will adhere to the JSON schema for a story, and will be returned as a JSON object. Below is reference for the schema for a story.",
            }
        ]
        schema = Story.model_json_schema()
        schema["additionalProperties"] = False
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
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                story_json = completion.choices[0].message.content
                story_json = json.loads(story_json)
                if "story" in story_json:
                    story_json = story_json["story"]
                new_story_json = {}
                for key in story_json:
                    new_key = key.lower()
                    if new_key != key:
                        new_story_json[new_key] = story_json[key]
                    else:
                        new_story_json[key] = story_json[key]
                story_json = new_story_json
                story = Story(**story_json)
                for character in story.starting_location.npcs_in_location:
                    character = self.postprocess_character(character)
                    
                story_json = json.loads(story.model_dump_json())
                if self.verbose:
                    # print(json.dumps(story_json,indent=4))
                    print_colored(json.dumps(story_json,indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Story Starter:",e)
                    print("Retrying...")
                pass
        return story
    
    def generate_story_from_character_card(self, character_card:CharacterCard):
        if self.verbose:
            # print("Generating Story from Character Card:",character_card.name)
            print_colored("Generating Story from Character Card: "+character_card.name, color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a story JSON to run the text adventure game with. It will adhere to the JSON schema for a story, and will be returned as a JSON object. Below is reference for the schema for a story.",
            }
        ]
        schema = Story.model_json_schema()
        schema["additionalProperties"] = False
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "user",
            "content": f"Generate a story based on the following character card:{character_card.model_dump_json()}"
        })
        # print(json.dumps(messages,indent=4))
        story = None
        while story == None:
            completion = None
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                story_json = completion.choices[0].message.content
                story_json = json.loads(story_json)
                new_story_json = {}
                for key in story_json:
                    new_key = key.lower()
                    if new_key != key:
                        new_story_json[new_key] = story_json[key]
                    else:
                        new_story_json[key] = story_json[key]
                story_json = new_story_json
                if self.verbose:
                    # print(json.dumps(story_json,indent=4))
                    print_colored(json.dumps(story_json,indent=4), color="green")
                story = Story(**story_json)
                for character in story.starting_location.npcs_in_location:
                    character = self.postprocess_character(character)
            except Exception as e:
                if self.verbose:
                    tb = traceback.format_exc()
                    print("Error Generating Story from Character Card:",e,tb,completion)
                    print("Retrying...")
                pass
        return story

    def generate_travelling_location(self, previous_location:Location, prompt:str):
        if self.verbose:
            # print("Generating Location for Prompt:",prompt)
            print_colored("Generating Location for Prompt: "+prompt, color="green")
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
                "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = Location.model_json_schema()
        schema["additionalProperties"] = False
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
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                location = Location(**location_json)
                if self.verbose:
                    # print(json.dumps(location_json,indent=4))
                    print_colored(json.dumps(location_json,indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Location:",e)
                    print("Retrying...")
                pass
        return location
    
    def generate_location(self, prompt:str):
        if self.verbose:
            # print("Generating Location for Prompt:",prompt)
            print_colored("Generating Location for Prompt: "+prompt, color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a location JSON to run the text adventure game with. It will adhere to the JSON schema for a location, and will be returned as a JSON object. Below is reference for the schema for a location.",
            },
            {
                "role": "system",
                "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = Location.model_json_schema()
        schema["additionalProperties"] = False
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
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                location = Location(**location_json)
                for character in location.npcs_in_location:
                    character = self.postprocess_character(character)
                if self.verbose:
                    # print(json.dumps(location_json,indent=4))
                    print_colored(json.dumps(location_json,indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Location:",e)
                    print("Retrying...")
                pass
        return location

    def generate_travelable_location(self, location:Location, prompt:str):
        if self.verbose:
            # print("Generating Travelable Location for Prompt:",prompt)
            print_colored("Generating Travelable Location for Prompt: "+prompt, color="green")
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
                "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = TravelableLocation.model_json_schema()
        schema["additionalProperties"] = False
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
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                travelable_location_json = completion.choices[0].message.content
                travelable_location_json = json.loads(travelable_location_json)
                travelable_location = TravelableLocation(**travelable_location_json)
                if self.verbose:
                    # print(json.dumps(travelable_location_json,indent=4))
                    print_colored(json.dumps(travelable_location_json,indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Travelable Location:",e)
                    print("Retrying...")
                pass
        return travelable_location

    def generate_travelable_location_between(self, prev_location:Location, next_location2:Location, previous_method_of_travel:str = None):
        if self.verbose:
            # print("Generating Travelable Location between:",prev_location.name,"and",next_location2.name)
            print_colored(f"Generating Travelable Location between '{prev_location.name}' and '{next_location2.name}'...", color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a travelable location JSON to run the text adventure game with. It will adhere to the JSON schema for a travelable location, and will be returned as a JSON object. Below is reference for the schema for a travelable location.",
            },
            {
                "role": "system",
                "content": f"The previous location was {prev_location.name}.\n{prev_location.location_physical_description}\nThe next location is {next_location2.name}.\n{next_location2.location_physical_description}\n"
            },
            {
                "role": "system",
                "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            }
        ]
        schema = TravelableLocation.model_json_schema()
        schema["additionalProperties"] = False
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "user",
            "content": f"Generate a travelable location between {prev_location.name} and {next_location2.name}."
        })
        messages.append({
            "role": "system",
            "content": schema_description
        })
        if previous_method_of_travel != None:
            messages.append({
                "role": "system",
                "content": f"The previous method of travel was: {previous_method_of_travel}\nThe next movement_description should be the reverse of this."
            })
        travelable_location = None
        while travelable_location == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                travelable_location_json = completion.choices[0].message.content
                travelable_location_json = json.loads(travelable_location_json)
                travelable_location = TravelableLocation(**travelable_location_json)
                if self.verbose:
                    # print(json.dumps(travelable_location_json,indent=4))
                    print_colored(json.dumps(travelable_location_json,indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Travelable Location:",e)
                    print("Retrying...")
                pass
        return travelable_location

    def set_story(self, story:Story):
        self.story_id = story.id
        self.story_vibe = story.vibe
        self.story_aesthetic = story.aesthetic
        for character in story.starting_location.npcs_in_location:
            character = self.postprocess_character(character)
        self.starting_location = story.starting_location
        self.current_location = story.starting_location
        self.locations.append(story.starting_location)
    
    def travel_to_location(self, travelable_location:TravelableLocation):
        print_colored("You are travelling to '"+travelable_location.location_name+"'...", color="green")
        next_location = None
        for loc in self.locations:
            if loc.name == travelable_location.location_name:
                next_location = loc
                break
        if next_location == None: # location doesn't exist yet
            if verbose:
                print_colored("Location doesn't exist yet, generating...", color="green")
            next_location = self.generate_location_from_travelable_location(travelable_location) # generate the location
            next_location.name = travelable_location.location_name
            self.locations.append(next_location)
        can_travel = False
        for t_location in self.current_location.travel_destinations:
            if t_location.portal == travelable_location.portal:
                can_travel = True
                break
        if can_travel:
            already_has_between_location = False
            for travelable_l in next_location.travel_destinations:
                if travelable_l.location_name == self.current_location.name:
                    # print("Already has a travelable location between",previous_location.name,"and",location.name)
                    already_has_between_location = True
                    break
            if not already_has_between_location: 
                portal_already_exists = False
                while not portal_already_exists:
                    between_location = self.generate_travelable_location_between(next_location, self.current_location, travelable_location.movement_description) # generate the travelable location for coming back
                    for t_location in self.current_location.travel_destinations:
                        if t_location.portal == between_location.portal:
                            portal_already_exists = True
                            break
                    if not portal_already_exists:
                        between_location.location_name = self.current_location.name
                        next_location.travel_destinations.append(between_location)
                        portal_already_exists = True
            # print(f"Travelling to {next_location.name}...")
            print(travelable_location.movement_description)
            # When travelling to a location, make sure you can't travel to the same location from that location
            for t_location in next_location.travel_destinations:
                if t_location.location_name == next_location.name:
                    next_location.travel_destinations.remove(t_location)
                    break
            if self.current_location in self.travel_order:
                self.travel_order.remove(self.current_location)
            self.travel_order.append(self.current_location) # add the previous location to the travel order
            if len(self.travel_order) > self.travel_order_length: # remove the oldest location from the travel order if it's longer than 5
                self.travel_order.pop(0)
            self.current_location = next_location
            return next_location
        else:
            print("You can't travel to that location from here!")
            return self.current_location
        
    def generate_location_from_travelable_location(self, travelable_location:TravelableLocation):
        if self.verbose:
            # print("Generating Location from Travelable Location:",travelable_location.location_name)
            print_colored("Generating Location from Travelable Location: "+json.dumps(travelable_location.model_dump_json(),indent=4), color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a location JSON to run the text adventure game with. It will adhere to the JSON schema for a location, and will be returned as a JSON object. Below is reference for the schema for a location.",
            },
            {
                "role": "system",
                "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            },
        ]
        if len(self.travel_order) > 0:
            for loc in self.travel_order:
                messages.append({
                    "role": "system",
                    "content": f"The user has previously visited {loc.name}.\n{loc.location_physical_description}"
                })
        messages.append({
            "role": "system",
            "content": f"The previous location was {self.current_location.name}.\n{self.current_location.location_physical_description}"
        })
        schema = Location.model_json_schema()
        schema["additionalProperties"] = False
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "user",
            "content": "Generate a location based on the following prompt:"+travelable_location.location_physical_description
        })
        messages.append({
            "role": "system",
            "content": schema_description
        })
        location = None
        while location == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                location = Location(**location_json)
                if self.verbose:
                    # print(json.dumps(location_json,indent=4))
                    print_colored(json.dumps(location_json,indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Location from Travelable Location:",e)
                    print("Retrying...")
                pass
        return location

    def generate_character_from_prompt(self, prompt:str):
        if self.verbose:
            # print("Generating Character for Prompt:",prompt)
            print_colored("Generating Character for Prompt: "+prompt, color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a character JSON to run the text adventure game with. It will adhere to the JSON schema for a character, and will be returned as a JSON object. Below is reference for the schema for a character.",
            },
            {
                "role": "system",
                "content": "The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            },
        ]
        if len(self.travel_order) > 0:
            for loc in self.travel_order:
                messages.append({
                    "role": "system",
                    "content": f"The user has previously visited {loc.name}.\n{loc.location_physical_description}"
                })
        messages.append({
            "role": "system",
            "content": f"The current location is {self.current_location.name}.\n{self.current_location.location_physical_description}"
        })
        schema = Character.model_json_schema()
        schema["additionalProperties"] = False
        schema_description = get_schema_description(schema)
        messages.append({
            "role": "user",
            "content": "Generate a character based on the following prompt:"+prompt
        })
        messages.append({
            "role": "system",
            "content": schema_description
        })
        character = None
        while character == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                character_json = completion.choices[0].message.content
                character_json = json.loads(character_json)
                character = Character(**character_json)
                character = self.postprocess_character(character)
                character_json = json.loads(character.model_dump_json())
                # print(json.dumps(character_json,indent=4))
                if self.verbose:
                    print_colored(json.dumps(character_json,indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    # print("Error Generating Character:",e)
                    print_colored("Error Generating Character: "+e, color="red")
                    print("Retrying...")
                pass
        return character
    
    def postprocess_character(self, character:Character):
        character.id = generate_id()
        if character.worn_clothing.headwear != None:
            if character.worn_clothing.headwear.name.lower() == "none" or character.worn_clothing.headwear.name.lower() == "null" or character.worn_clothing.headwear.name.strip() == "":
                character.worn_clothing.headwear = None
        if character.worn_clothing.upperbodywear != None:
            if character.worn_clothing.upperbodywear.name.lower() == "none" or character.worn_clothing.upperbodywear.name.lower() == "null" or character.worn_clothing.upperbodywear.name.strip() == "":
                character.worn_clothing.upperbodywear = None
        if character.worn_clothing.fullbodywear != None:
            if character.worn_clothing.fullbodywear.name.lower() == "none" or character.worn_clothing.fullbodywear.name.lower() == "null" or character.worn_clothing.fullbodywear.name.strip() == "":
                character.worn_clothing.fullbodywear = None
        if character.worn_clothing.upperbody_underwear != None:
            if character.worn_clothing.upperbody_underwear.name.lower() == "none" or character.worn_clothing.upperbody_underwear.name.lower() == "null" or character.worn_clothing.upperbody_underwear.name.strip() == "":
                character.worn_clothing.upperbody_underwear = None
        if character.worn_clothing.gloves != None:
            if character.worn_clothing.gloves.name.lower() == "none" or character.worn_clothing.gloves.name.lower() == "null" or character.worn_clothing.gloves.name.strip() == "":
                character.worn_clothing.gloves = None
        if character.worn_clothing.bottom_underwear != None:
            if character.worn_clothing.bottom_underwear.name.lower() == "none" or character.worn_clothing.bottom_underwear.name.lower() == "null" or character.worn_clothing.bottom_underwear.name.strip() == "":
                character.worn_clothing.bottom_underwear = None
        if character.worn_clothing.lowerbodywear != None:
            if character.worn_clothing.lowerbodywear.name.lower() == "none" or character.worn_clothing.lowerbodywear.name.lower() == "null" or character.worn_clothing.lowerbodywear.name.strip() == "":
                character.worn_clothing.lowerbodywear = None
        if character.worn_clothing.footwear != None:
            if character.worn_clothing.footwear.name.lower() == "none" or character.worn_clothing.footwear.name.lower() == "null" or character.worn_clothing.footwear.name.strip() == "":
                character.worn_clothing.footwear = None
        if character.equiped_weapon != None:
            if character.equiped_weapon.name.lower() == "none" or character.equiped_weapon.name.lower() == "null" or character.equiped_weapon.name.strip() == "":
                character.equiped_weapon = None
        if character.worn_clothing.accessories != None:
            for item in character.worn_clothing.accessories:
                if item.name.lower() == "none" or item.name.lower() == "null" or item.name.strip() == "":
                    character.worn_clothing.accessories.remove(item)
        for item in character.inventory:
            if item.name.lower() == "none" or item.name.lower() == "null" or item.name.strip() == "":
                character.inventory.remove(item)
        return character

    def generate_character_from_character_card(self, character_card:CharacterCard, instruction:str = "", user:bool = False):
        if self.verbose:
            # print("Generating Character from Character Card:",character_card.name)
            print_colored("Generating Character from Character Card: "+character_card.name, color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a character JSON to run the text adventure game with. It will adhere to the JSON schema for a character, and will be returned as a JSON object. Below is reference for the schema for a character.",
            },
            {
                "role": "system",
                "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
            },
        ]
        if len(self.travel_order) > 0:
            for loc in self.travel_order:
                messages.append({
                    "role": "system",
                    "content": f"The user has previously visited {loc.name}.\n{loc.location_physical_description}"
                })
        messages.append({
            "role": "system",
            "content": f"The current location is {self.current_location.name}.\n{self.current_location.location_physical_description}"
        })
        schema = Character.model_json_schema()
        schema["additionalProperties"] = False
        schema_description = get_schema_description(schema)
        if user:
            messages.append({
                "role": "user",
                "content": f"Note, this character should not be the character that the assistant will play, but the one the user will play. Generate the user's character based on the following character card: {character_card.model_dump_json()}"
            })
        else:
            messages.append({
                "role": "user",
                "content": f"Generate a character based on the following character card: {character_card.model_dump_json()}"
            })
        if instruction != "":
            messages.append({
                "role": "user",
                "content": instruction
            })
        messages.append({
            "role": "system",
            "content": schema_description
        })
        character = None
        while character == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                character_json = completion.choices[0].message.content
                character_json = json.loads(character_json)
                if self.verbose:
                    # print(json.dumps(character_json,indent=4))
                    print_colored(json.dumps(character_json,indent=4), color="green")
                character = Character(**character_json)
                character = self.postprocess_character(character)
            except Exception as e:
                if self.verbose:
                    print("Error Generating Character from Character Card:",e)
                    print("Retrying...")
                pass
        return character

    def generate_item_from_prompt(self, prompt:str):
        if self.verbose:
            # print("Generating Item for Prompt:",prompt)
            print_colored("Generating Item for Prompt: "+prompt, color="green")
        messages = []
        schema = SomeItem.model_json_schema()
        schema["additionalProperties"] = False
        schema_description = get_schema_description(schema)
        # if verbose:
        #     print_colored("Generated Item Schema Description: "+schema_description, color="green")
        messages.append({
            "role": "system",
            "content": schema_description
        })
        messages.append({
            "role": "system",
            "content": "The assistant is generating an item JSON to run the text adventure game with. It will adhere to the JSON schema for an item, and will be returned as a JSON object. Below is reference for the schema for an item.",
        })
        messages.append({
            "role": "system",
            "content": f"The current location is {self.current_location.name}.\n{self.current_location.location_physical_description}"
        })
        messages.append({
            "role": "system",
            "content": f"The vibe is {self.story_vibe} and the aesthetic is {self.story_aesthetic}."
        })
        messages.append({
            "role": "user",
            "content": "Generate an item based on the following prompt:"+prompt
        })
        item = None
        while item == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                item_json = completion.choices[0].message.content
                item_json = json.loads(item_json)
                item = SomeItem(**item_json)
                item = item.item
                # item.position_in_location = "on the ground"
                if self.verbose:
                    # print(json.dumps(json.loads(item.model_dump_json()),indent=4))
                    print_colored(json.dumps(json.loads(item.model_dump_json()),indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Item:",e)
                    print("Retrying...")
                pass
        return item
    
    def find_item(self, prompt:str = None):
        """Finding an item in the current location - Takes the prompt and asks the LLM if it can find it in the current location, and if it can, return it as a list of item prompts"""
        if prompt == None:
            if self.verbose:
                print("Generating... Deciding if there is more stuff in the current location...")
        else:
            if self.verbose:
                # print("Generating Item for Prompt:",prompt)
                print_colored("Generating Item for Prompt: "+prompt, color="green")
        messages = []
        some_item_schema = SomeItem.model_json_schema()
        some_item_schema["additionalProperties"] = False
        some_item_schema_description = get_schema_description(some_item_schema)
        messages.append({
            "role": "system",
            "content": some_item_schema_description
        })
        prompts_schema = Prompts.model_json_schema()
        prompts_schema["additionalProperties"] = False
        prompts_schema_description = get_schema_description(prompts_schema)
        # add location description
        messages.append({
            "role": "system",
            "content": get_current_screen()
        })
        messages.append({
            "role": "system",
            "content": "The assistant is generating an item JSON to run the text adventure game with. It will adhere to the JSON schema for an item, and will be returned as a JSON object. Below is reference for the schema for an item.",
        })
        if prompt == None:
            messages.append({
                "role": "user",
                "content": f"The user is looking around the current location. The assistant should return lists of stuff that can be found in the current location based on what they're looking for. These lists should not include the stuff already in the location. The stuff should be in the format of the following JSON schema:\n\n{prompts_schema_description}\nIf nothing else should be found here, or it would be nonsensical to find what the user is looking for here, then return nothing in the prompts lists."
            })
        else:
            messages.append({
                "role": "user",
                "content": f"The user is looking for an item in the current location. The assistant should return lists of stuff that can be found in the current location based on what they're looking for. These lists should not include the stuff already in the location. The stuff should be in the format of the following JSON schema:\n\n{prompts_schema_description}\nIf the user can't find what they're looking for here, then return nothing in the prompts lists. If nothing else should be found here, or it would be nonsensical to find what the user is looking for here, then return nothing in the prompts lists.\n\nThe user is looking for the following: {prompt}"
            })
        prompts = None
        while prompts == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(prompts_schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": prompts_schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                prompts_json = completion.choices[0].message.content
                prompts_json = json.loads(prompts_json)
                prompts = Prompts(**prompts_json)
                if self.verbose:
                    # print(json.dumps(json.loads(prompts.model_dump_json()),indent=4))
                    print_colored(json.dumps(json.loads(prompts.model_dump_json()),indent=4), color="green")
            except Exception as e:
                if self.verbose:
                    print("Error Generating Item:",e)
                    print("Retrying...")
                pass
        found = {
            "items": [],
            "characters": [],
            "travelable_locations": []
        }
        for prmpt in prompts.prompts:
            if prmpt.prompt_type.lower() == "item":
                already_exists = False
                for item2 in self.current_location.objects_in_location:
                    if prmpt.prompt.lower() in item2.name.lower():
                        already_exists = True
                        break
                if already_exists:
                    if self.verbose:
                        # print(f"Item '{prmpt.prompt}' already exists in location, not generating...")
                        print_colored(f"Item '{prmpt.prompt}' already exists in location, not generating...", color="red")
                    continue
                else:
                    item:SomeItem = self.generate_item_from_prompt(prompt+" "+prmpt.prompt)
                    found["items"].append(item)
            elif prmpt.prompt_type.lower() == "character":
                already_exists = False
                for char in self.current_location.npcs_in_location:
                    if prmpt.prompt.lower() in char.full_name.lower():
                        already_exists = True
                        break
                if already_exists:
                    if self.verbose:
                        # print(f"Character '{prmpt.prompt}' already exists in location, not generating...")
                        print_colored(f"Character '{prmpt.prompt}' already exists in location, not generating...", color="red")
                    continue
                else:
                    character:CharacterCard = self.generate_character_from_prompt(prompt+" "+prmpt.prompt)
                    found["characters"].append(character)
            elif prmpt.prompt_type.lower() == "travelablelocation":
                already_exists = False
                for travelable_location in self.current_location.travel_destinations:
                    if prmpt.prompt.lower() in travelable_location.location_name.lower():
                        already_exists = True
                        break
                if already_exists:
                    if self.verbose:
                        # print(f"Travelable Location '{prmpt.prompt}' already exists in location, not generating...")
                        print_colored(f"Travelable Location '{prmpt.prompt}' already exists in location, not generating...", color="red")
                    continue
                else:
                    travelable_location:TravelableLocation = self.generate_travelable_location(self.current_location, prompt+" "+prmpt.prompt)
                    found["travelable_locations"].append(travelable_location)
        return found

    def generate_decisions_for_character(self, character:Character):
        if self.verbose:
            # print("Generating Decisions for Character:",character.full_name)
            print_colored("Generating Decisions for Character: "+character.full_name, color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating decisions for a character in the text adventure game. It will adhere to the JSON schema for decisions, and will be returned as a JSON object. Below is reference for the schema for decisions.",
            }
        ]
        location_names = []
        for travelable_location in self.current_location.travel_destinations:
            location_names.append(travelable_location.location_name)
        location_names_pattern = "|".join(location_names)
        class TravelDecision(BaseModel):
            """Travel Decision Schema - A decision made by an NPC to travel to a new location in the text adventure game. All fields are required to have a value."""
            type_string: str = Field(description="The type of decision.", pattern="^Travel$")
            location: str = Field(description="The location that the NPC wants to travel to.", min_length=1, pattern=f"^({location_names_pattern})$")

            def __init__(self, **data):
                super().__init__(**data)

            @staticmethod
            def model_example():
                return {
                    "type_string": "Travel",
                    "location": "The Dark Cave"
                }
            
        class Decisions(BaseModel):
            """Decision Schema - A decision made by an NPC in the text adventure game. All fields are required to have a value."""
            decisions: list[Union[TravelDecision,SayDecision,ActionDecision,TakeDecision,DropDecision,AttackDecision,EquipDecision,UnequipDecision]] = Field(description="A list of decisions made by the NPC. Each decision should have a type_string, and the appropriate fields for that type of decision. All decisions made by the NPC in the text adventure game.", min_length=1)

        schema = Decisions.model_json_schema()
        schema["additionalProperties"] = False
        for schema_key in schema["$defs"]:
            if schema_key == "decisions":
                schema["$defs"][schema_key]["additionalProperties"] = False
        # if self.verbose:
            # print(json.dumps(schema,indent=4))
            # print_colored("Schema: "+json.dumps(schema,indent=4), color="green")
        schema_description = get_schema_description(schema)
        decision_types: list[Union[TravelDecision,SayDecision,ActionDecision,TakeDecision,DropDecision,AttackDecision,EquipDecision,UnequipDecision]] = [TravelDecision,SayDecision,ActionDecision,TakeDecision,DropDecision,AttackDecision,EquipDecision,UnequipDecision]
        for decision_type in decision_types:
            schema_description += "\n"+get_schema_description(decision_type.model_json_schema())
        schema_description += "\n\nThe following are examples of the decisions that can be made:\n"
        for decision_type in decision_types:
            schema_description += "\n"+json.dumps(decision_type.model_example(),indent=4)
        # location
        messages.append({
            "role": "system",
            "content": f"The current location is {self.current_location.name}.\n{self.current_location.location_physical_description}"
        })
        # schema description
        messages.append({
            "role": "system",
            "content": schema_description
        })
        for char in self.current_location.npcs_in_location:
            messages.append({
                "role": "system",
                "content": f"{char.full_name} is here.\n{char.get_physical_description()}"
            })
        # item descriptions
        for item in self.current_location.objects_in_location:
            messages.append({
                "role": "system",
                "content": f"{item.name} is here.\n{item.physical_description}"
            })
        # travelable locations
        for travelable_location in self.current_location.travel_destinations:
            messages.append({
                "role": "system",
                "content": f"Travel Option: {travelable_location.portal} is here.\nUse a word or selection of words from this string to travel here:{travelable_location.location_name}\nDescription: {travelable_location.location_physical_description}"
            })
        # # player character
        messages.append({
            "role": "system",
            "content": f"{self.player.full_name} is here.\n{self.player.get_physical_description()}"
        })
        # # character description
        messages.append({
            "role": "system",
            "content": f"{character.get_description()}"
        })
        # character inventory
        messages.append({
            "role": "system",
            "content": f"{character.full_name}'s inventory is:\n{character.get_inventory_description()}"
        })
        history = self.messages_db.get()
        recent_messages = []
        for msg_id, msg_doc, msg_metadata in zip(history["ids"], history["documents"], history["metadatas"]):
            present = msg_metadata["present"].split(", ")
            if (character.id in present or msg_metadata["speaker_id"] == character.id or msg_metadata["role"] == "user") and msg_metadata["story_id"] == self.story_id:
                if msg_metadata["roleplay"]:
                    recent_messages.append({
                        "role": msg_metadata["role"],
                        "content": "Roleplayed Action: "+msg_metadata["speaker_name"] + " " + msg_doc + ".",
                        "timestamp": msg_metadata["timestamp"]
                    })
                else:
                    recent_messages.append({
                        "role": msg_metadata["role"],
                        "content": msg_metadata["speaker_name"] + ": " + msg_doc,
                        "timestamp": msg_metadata["timestamp"]
                    })
        recent_messages.sort(key=lambda x: x["timestamp"])
        
        messages.extend(recent_messages)
        messages.append({
            "role": "user",
            "content": f"Generate decisions for the character '{character.full_name}'. They should only do, or not do, what they would do in this situation. If the character doesn't want to do anything, then return nothing in the decisions lists."
        })
        # messages.append({
        #     "role": "system",
        #     "content": f"Generate decisions for the character {character.full_name}."
        # })
        if self.verbose:
            # print(json.dumps(messages,indent=4))
            print_colored(json.dumps(messages,indent=4), color="green")
        decisions = None
        while decisions == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                if self.verbose:
                    print("Completion:",completion)
                decisions_json = completion.choices[0].message.content
                decisions_json = json.loads(decisions_json)
                if self.verbose:
                    # print(json.dumps(decisions_json,indent=4))
                    print_colored(json.dumps(decisions_json,indent=4), color="green")
                new_decisions_json = {}
                for key in decisions_json:
                    new_key = key.lower()
                    if new_key != key:
                        new_decisions_json[new_key] = decisions_json[key]
                    else:
                        new_decisions_json[key] = decisions_json[key]
                decisions_json = new_decisions_json
                if self.verbose:
                    # print(json.dumps(decisions_json,indent=4))
                    print_colored(json.dumps(decisions_json,indent=4), color="green")
                decisions = Decisions(**decisions_json)
            except Exception as e:
                if self.verbose:
                    print("Error Generating Decisions for Character:",e)
                    print("Retrying...")
                pass
        return decisions

    def generate_decisions_for_game_master(self):
        if self.verbose:
            # print("Generating Decisions for Game Master")
            print_colored("Generating Decisions for Game Master", color="green")
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating decisions for the game master in the text adventure game. It will adhere to the JSON schema for decisions, and will be returned as a JSON object. Below is reference for the schema for decisions.",
            }
        ]
        location_names = []
        for travelable_location in self.current_location.travel_destinations:
            location_names.append(travelable_location.location_name)
        location_names_pattern = "|".join(location_names)
        class UserTravelDecision(BaseModel):
            """User Travel Decision Schema - A decision made by the game master to teleport a user to a new location in the text adventure game. Teleports don't leave a path between where they were and where they went. All fields are required to have a value."""
            type_string: str = Field(description="The type of decision.", pattern="^UserTravel$")
            location: str = Field(description="The location that the game master wants to teleport the player to.", min_length=1, pattern=f"^({location_names_pattern})$")

            def __init__(self, **data):
                super().__init__(**data)
            @staticmethod
            def model_example():
                return {
                    "type_string": "UserTravel",
                    "location": "The Dark Cave"
                }
            
        class GameMasterDecisions(BaseModel):
            """Game Master Decision Schema - A decision made by the game master in the text adventure game. All fields are required to have a value."""
            decisions: list[Union[TeleportDecision,UserTravelDecision,SpawnCharacterDecision,SpawnItemDecision,SpawnNewLocationDecision,FurtherDescribeCurrentLocationDecision,GivePlayerItemDecision,DamageDecision,KillDecision,EquipItemDecision,UnequipItemDecision,DropItemDecision,PickUpItemDecision]] = Field(description="A list of decisions made by the game master. Each decision should have a type_string, and the appropriate fields for that type of decision. All decisions made by the game master in the text adventure game.")
        schema = GameMasterDecisions.model_json_schema()
        schema["additionalProperties"] = False
        for schema_key in schema["$defs"]:
            if schema_key == "decisions":
                schema["$defs"][schema_key]["additionalProperties"] = False
        # if self.verbose:
            # print(json.dumps(schema,indent=4))
            # print_colored("Schema: "+json.dumps(schema,indent=4), color="green")
        schema_description = get_schema_description(schema)
        decision_types: list[Union[TeleportDecision,UserTravelDecision,SpawnCharacterDecision,SpawnItemDecision,SpawnNewLocationDecision,FurtherDescribeCurrentLocationDecision,GivePlayerItemDecision,DamageDecision,KillDecision,EquipItemDecision,UnequipItemDecision,DropItemDecision,PickUpItemDecision]] = [TeleportDecision,UserTravelDecision,SpawnCharacterDecision,SpawnItemDecision,SpawnNewLocationDecision,FurtherDescribeCurrentLocationDecision,GivePlayerItemDecision,DamageDecision,KillDecision,EquipItemDecision,UnequipItemDecision,DropItemDecision,PickUpItemDecision]
        for decision_type in decision_types:
            schema_description += "\n"+get_schema_description(decision_type.model_json_schema())
        schema_description += "\n\nThe following are examples of the decisions that can be made:\n"
        for decision_type in decision_types:
            schema_description += "\n"+json.dumps(decision_type.model_example(),indent=4)
        # location
        messages.append({
            "role": "system",
            "content": f"The current location is {self.current_location.name}.\n{self.current_location.location_physical_description}"
        })
        # schema description
        messages.append({
            "role": "system",
            "content": schema_description
        })
        for char in self.current_location.npcs_in_location:
            messages.append({
                "role": "system",
                "content": f"{char.full_name} is here.\n{char.get_physical_description()}"
            })
        # item descriptions
        for item in self.current_location.objects_in_location:
            messages.append({
                "role": "system",
                "content": f"{item.name} is here.\n{item.physical_description}"
            })
        # travelable locations
        for travelable_location in self.current_location.travel_destinations:
            messages.append({
                "role": "system",
                "content": f"Travel Option: {travelable_location.portal} is here.\nUse a word or selection of words from this string to travel here:{travelable_location.location_name}\nDescription: {travelable_location.location_physical_description}"
            })
        # # player character
        messages.append({
            "role": "system",
            "content": f"{self.player.full_name} is here.\n{self.player.get_physical_description()}"
        })
        # # character description
        messages.append({
            "role": "system",
            "content": f"{self.player.get_description()}"
        })
        # character inventory
        messages.append({
            "role": "system",
            "content": f"{self.player.full_name}'s inventory is:\n{self.player.get_inventory_description()}"
        })
        # history
        history = self.messages_db.get()
        recent_messages = []
        for msg_id, msg_doc, msg_metadata in zip(history["ids"], history["documents"], history["metadatas"]):
            if msg_metadata["story_id"] == self.story_id:
                if msg_metadata["roleplay"]:
                    recent_messages.append({
                        "role": msg_metadata["role"],
                        "content": "Roleplayed Action: "+msg_metadata["speaker_name"] + " " + msg_doc + ".",
                        "timestamp": msg_metadata["timestamp"]
                    })
                else:
                    recent_messages.append({
                        "role": msg_metadata["role"],
                        "content": msg_metadata["speaker_name"] + ": " + msg_doc,
                        "timestamp": msg_metadata["timestamp"]
                    })
        recent_messages.sort(key=lambda x: x["timestamp"])
        messages.extend(recent_messages)
        messages.append({
            "role": "user",
            "content": f"Generate decisions for the game master. The Game Master decides how the world reacts to players and NPCs. If the Game Master doesn't want to do anything, then return nothing in the decisions lists. If the roleplay of the characters tries to interact with the world, the game master's job is to facilitate that interaction. The Game Master should not be a character in the game, but rather a facilitator of the game. If the player didn't interact with something, and it's not being interacted with by another NPC, don't do anything with it. If someone hasn't used a roleplay action to move, don't make them travel. Saying they want to go somewhere isn't the same as going somewhere. If the assistant roleplays travelling, then the Game Master should not try to make them travel. The UserTravel decision is only usable by the user. The user's character is {self.player.full_name}. If the user hasn't done anything, and the game master doesn't want to do anything, then return nothing in the decisions lists. Don't randomly give the user items without a reason for them to have been given them."
        })
        if self.verbose:
            # print(json.dumps(messages,indent=4))
            print_colored(json.dumps(messages,indent=4), color="green")
        decisions = None
        while decisions == None:
            try:
                if openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": pydantic_to_open_router_schema(schema)
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                else:
                    completion = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        response_format={
                            "type": "json_schema",
                            "json_schema": schema
                        },
                        extra_body={
                            "min_p": self.min_p,
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                if self.verbose:
                    print("Completion:",completion)
                decisions_json = completion.choices[0].message.content
                decisions_json = json.loads(decisions_json)
                if self.verbose:
                    # print(json.dumps(decisions_json,indent=4))
                    print_colored(json.dumps(decisions_json,indent=4), color="green")
                new_decisions_json = {}
                for key in decisions_json:
                    new_key = key.lower()
                    if new_key != key:
                        new_decisions_json[new_key] = decisions_json[key]
                    else:
                        new_decisions_json[key] = decisions_json[key]
                decisions_json = new_decisions_json
                if self.verbose:
                    # print(json.dumps(decisions_json,indent=4))
                    print_colored(json.dumps(decisions_json,indent=4), color="green")
                decisions = GameMasterDecisions(**decisions_json)
            except Exception as e:
                if self.verbose:
                    print("Error Generating Decisions for Game Master:",e)
                    print("Retrying...")
                pass
        return decisions

    def say(self, character:Character, message:str, is_user:bool = False,should_print = True, should_add_to_db = True):
        if should_add_to_db:
            npcs_present = self.current_location.npcs_in_location
            npc_ids_present = [npc.id for npc in npcs_present]
            metadata = {
                "story_id": self.story_id,
                "speaker_id": character.id,
                "location_id": self.current_location.id,
                "speaker_name": character.full_name,
                "role": "user" if is_user else "assistant",
                "present": ", ".join(npc_ids_present),
                "roleplay": False,
                "timestamp": time.time(),
            }
            if self.verbose:
                # print("Metadata:",metadata)
                print_colored("Metadata: "+json.dumps(metadata,indent=4), color="green")
            message_id = generate_id()
            self.messages_db.add(documents=[message], metadatas=[metadata], ids=[message_id])
        if should_print:
            if character.hex_color == None:
                character.hex_color = "FFFFFF"
            if character.hex_color == "":
                character.hex_color = "FFFFFF"
            print(f"{fore_fromhex('#'+character.hex_color)}{character.full_name}{bcolors.ENDC} {bcolors.GREY}says:{bcolors.ENDC} {message}")

    def roleplay(self, character:Character, message:str, is_user:bool = False, should_print = True, should_add_to_db = True):
        if should_add_to_db:
            npcs_present = self.current_location.npcs_in_location
            npc_ids_present = [npc.id for npc in npcs_present]
            metadata = {
                "story_id": self.story_id,
                "speaker_id": character.id,
                "location_id": self.current_location.id,
                "speaker_name": character.full_name,
                "role": "user" if is_user else "assistant",
                "present": ", ".join(npc_ids_present),
                "roleplay": True,
                "timestamp": time.time(),
            }
            if self.verbose:
                print(metadata)
            message_id = generate_id()
            if message.endswith("."):
                message = message[:-1]
            self.messages_db.add(documents=[message], metadatas=[metadata], ids=[message_id])
        if should_print:
            print(f"{character.full_name} {message}.")

    def ai_turn(self):
        character_decisions_queue = []
        for character in tqdm(self.current_location.npcs_in_location, desc="AI Turn", unit="character"):
            # if character not in self.met:
            #     self.met.append(character)
            if character.stats.hp > 0 and character.processing:
                # print(f"{character.full_name} is taking their turn...")
                if verbose:
                    print_colored(f"\n{character.full_name} is taking their turn...", color="yellow")
                decisions = text_adventure.generate_decisions_for_character(character)
                for decision in decisions.decisions:
                    if decision.type_string.lower() == "say":
                        self.say(character, decision.message,should_print=False)
                    elif decision.type_string.lower() == "action":
                        self.roleplay(character, decision.message,should_print=False)
                character_decisions_queue.append((character, decisions))
        for character, decisions in character_decisions_queue:
            for decision in decisions.decisions:
                if decision.type_string.lower() == "say":
                    self.say(character, decision.message,should_add_to_db=False)
                elif decision.type_string.lower() == "action":
                    self.roleplay(character, decision.message,should_add_to_db=False)
                elif decision.type_string.lower() == "travel":
                    if verbose:
                        print_colored(f"{character.full_name} is trying to travel...", color="yellow")
                    self.roleplay(character, f"tries to travel to {decision.location}.",should_print=False)
                    for t_location in self.current_location.travel_destinations:
                        if decision.location.lower() in t_location.portal.lower() or decision.location.lower() in t_location.location_name.lower():
                            if verbose:
                                print_colored(f"{character.full_name} is traveling to {t_location.location_name}...", color="yellow")
                            self.roleplay(character, f"travels to {t_location.location_name}.",should_print=False)
                            self.npc_travel(character, t_location)
                elif decision.type_string.lower() == "pickup":
                    for item in self.current_location.objects_in_location:
                        if item.name == decision.item:
                            character.inventory.append(item)
                            self.current_location.objects_in_location.remove(item)
                            print(f"{character.full_name} picks up the {item.name}.")
                            break
                elif decision.type_string.lower() == "drop":
                    for item in character.inventory:
                        if item.name == decision.item:
                            character.inventory.remove(item)
                            self.current_location.objects_in_location.append(item)
                            print(f"{character.full_name} drops the {item.name}.")
                            break
                    if character.equiped_weapon != None:
                        if character.equiped_weapon.name == decision.item:
                            character.equiped_weapon = None
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    if character.worn_clothing.headwear != None:
                        if character.worn_clothing.headwear.name == decision.item:
                            character.worn_clothing.headwear = None
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    if character.worn_clothing.upperbodywear != None:
                        if character.worn_clothing.upperbodywear.name == decision.item:
                            character.worn_clothing.upperbodywear = None
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    if character.worn_clothing.fullbodywear != None:
                        if character.worn_clothing.fullbodywear.name == decision.item:
                            character.worn_clothing.fullbodywear = None
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    if character.worn_clothing.gloves != None:
                        if character.worn_clothing.gloves.name == decision.item:
                            character.worn_clothing.gloves = None
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    if character.worn_clothing.lowerbodywear != None:
                        if character.worn_clothing.lowerbodywear.name == decision.item:
                            character.worn_clothing.lowerbodywear = None
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    if character.worn_clothing.footwear != None:
                        if character.worn_clothing.footwear.name == decision.item:
                            character.worn_clothing.footwear = None
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    for item in character.worn_clothing.accessories:
                        if item.name == decision.item:
                            character.worn_clothing.accessories.remove(item)
                            print(f"{character.full_name} unequips the {decision.item}.")
                            break
                    if character.equiped_weapon != None:
                        if character.equiped_weapon.name == decision.item:
                            character.equiped_weapon = None
                            # print(f"{character.full_name} unequips the {decision.item}.")
                            self.roleplay(character, f"unequips the {decision.item}.")
                            break
                elif decision.type_string.lower() == "equip":
                    for item in character.inventory:
                        if decision.item.lower() in item.name.lower():
                            if item.type_string == "Weapon":
                                character.equiped_weapon = item
                                print(f"{character.full_name} equips the {item.name}.")
                            else:
                                if item.type_string == "Headwear":
                                    character.worn_clothing.headwear = item
                                elif item.type_string == "Upperbodywear":
                                    character.worn_clothing.upperbodywear = item
                                elif item.type_string == "Upperbody Underwear":
                                    character.worn_clothing.upperbody_underwear = item
                                elif item.type_string == "Fullbodywear":
                                    character.worn_clothing.fullbodywear = item
                                elif item.type_string == "Gloves":
                                    character.worn_clothing.gloves = item
                                elif item.type_string == "Lowerbodywear":
                                    character.worn_clothing.lowerbodywear = item
                                elif item.type_string == "Bottom Underwear":
                                    character.worn_clothing.bottom_underwear = item
                                elif item.type_string == "Footwear":
                                    character.worn_clothing.footwear = item
                                elif item.type_string == "Accessory":
                                    character.worn_clothing.accessories.append(item)
                                print(f"{character.full_name} equips the {item.name}.")
                            break
                elif decision.type_string.lower() == "unequip":
                    if decision.item == "Weapon":
                        character.equiped_weapon = None
                        print(f"{character.full_name} unequips their Weapon: {decision.item}.")
                    elif character.worn_clothing.headwear != None and decision.item in character.worn_clothing.headwear.name:
                        print(f"{character.full_name} unequips their Headwear: {character.worn_clothing.headwear.name}.")
                        character.worn_clothing.headwear = None
                    elif character.worn_clothing.upperbodywear != None and decision.item.lower() in character.worn_clothing.upperbodywear.name.lower():
                        print(f"{character.full_name} unequips their Upperbodywear: {character.worn_clothing.upperbodywear.name}.")
                        character.worn_clothing.upperbodywear = None
                    elif character.worn_clothing.upperbody_underwear != None and decision.item.lower() in character.worn_clothing.upperbody_underwear.name.lower():
                        print(f"{character.full_name} unequips their Upperbody Underwear: {character.worn_clothing.upperbody_underwear.name}.")
                        character.worn_clothing.upperbody_underwear = None
                    elif character.worn_clothing.fullbodywear != None and decision.item.lower() in character.worn_clothing.fullbodywear.name.lower():
                        print(f"{character.full_name} unequips their Fullbodywear: {character.worn_clothing.fullbodywear.name}.")
                        character.worn_clothing.fullbodywear = None
                    elif character.worn_clothing.gloves != None and decision.item.lower() in character.worn_clothing.gloves.name.lower():
                        print(f"{character.full_name} unequips their Gloves: {character.worn_clothing.gloves.name}.")
                        character.worn_clothing.gloves = None
                    elif character.worn_clothing.lowerbodywear != None and decision.item.lower() in character.worn_clothing.lowerbodywear.name.lower():
                        print(f"{character.full_name} unequips their Lowerbodywear: {character.worn_clothing.lowerbodywear.name}.")
                        character.worn_clothing.lowerbodywear = None
                    elif character.worn_clothing.bottom_underwear != None and decision.item.lower() in character.worn_clothing.bottom_underwear.name.lower():
                        print(f"{character.full_name} unequips their Bottom Underwear: {character.worn_clothing.bottom_underwear.name}.")
                        character.worn_clothing.bottom_underwear = None
                    elif character.worn_clothing.footwear != None and decision.item.lower() in character.worn_clothing.footwear.name.lower():
                        print(f"{character.full_name} unequips their Footwear: {character.worn_clothing.footwear.name}.")
                        character.worn_clothing.footwear = None
                    elif character.worn_clothing.accessories != None:
                        for item in character.worn_clothing.accessories:
                            if decision.item.lower() in item.name.lower():
                                print(f"{character.full_name} unequips the Accessory {item.name}.")
                                character.worn_clothing.accessories.remove(item)
                                break
                        # if decision.item == "Headwear":
                        #     character.worn_clothing.headwear = None
                        #     print(f"{character.full_name} unequips their Headwear: {decision.item}.")
                        # elif decision.item == "Upperbodywear":
                        #     character.worn_clothing.upperbodywear = None
                        #     print(f"{character.full_name} unequips their Upperbodywear: {decision.item}.")
                        # elif decision.item == "Fullbodywear":
                        #     character.worn_clothing.fullbodywear = None
                        #     print(f"{character.full_name} unequips their Fullbodywear: {decision.item}.")
                        # elif decision.item == "Gloves":
                        #     character.worn_clothing.gloves = None
                        #     print(f"{character.full_name} unequips their Gloves: {decision.item}.")
                        # elif decision.item == "Lowerbodywear":
                        #     character.worn_clothing.lowerbodywear = None
                        #     print(f"{character.full_name} unequips their Lowerbodywear: {decision.item}.")
                        # elif decision.item == "Footwear":
                        #     character.worn_clothing.footwear = None
                        #     print(f"{character.full_name} unequips their Footwear: {decision.item}.")
                        # elif decision.item == "Accessory":
                        #     for item in character.worn_clothing.accessories:
                        #         if decision.item.lower() in item.name.lower():
                        #             character.worn_clothing.accessories.remove(item)
                        #             print(f"{character.full_name} unequips the Accessory {decision.item}.")
                        #             break

    def game_master_turn(self):
        decisions = text_adventure.generate_decisions_for_game_master()
        print(bcolors.GREEN,decisions,bcolors.ENDC)
        for decision in decisions.decisions:
            if decision.type_string.lower() == "teleport":
                teleport_location = None
                for loc in self.locations:
                    if loc.name == decision.location:
                        teleport_location = loc
                        break
                if teleport_location == None:
                    if verbose:
                        print_colored(f"Teleport location '{decision.location}' not found.", color="red")
                teleport_target = None
                teleport_target_is_player = False
                for char in self.current_location.npcs_in_location:
                    if decision.character.lower() in char.full_name.lower():
                        teleport_target = char
                        break
                if teleport_target == None:
                    if decision.character.lower() in self.player.full_name.lower():
                        teleport_target = self.player
                        teleport_target_is_player = True
                if teleport_target == None:
                    if verbose:
                        print_colored(f"{decision.character} not found in location.", color="red")
                if teleport_target != None and teleport_location != None:
                    if teleport_target_is_player:
                        self.current_location = teleport_location
                        print(f"{teleport_target.full_name} teleports to {teleport_location.name}.")
                    else:
                        self.current_location.npcs_in_location.remove(teleport_target)
                        teleport_location.npcs_in_location.append(teleport_target)
                        print(f"{teleport_target.full_name} teleports away.")
            elif decision.type_string.lower() == "usertravel":
                if verbose:
                    print_colored(f"User Travel: {decision.location}", color="yellow")
                text_adventure.player_travel(decision.location)
            elif decision.type_string.lower() == "spawncharacter":
                character = self.generate_character_from_prompt(decision.character)
                if character != None:
                    self.current_location.npcs_in_location.append(character)
                    print(f"{character.full_name} spawns in {self.current_location.name}.")
            elif decision.type_string.lower() == "spawngamecharacter":
                character = self.generate_character_from_prompt(decision.character)
                if character != None:
                    self.current_location.npcs_in_location.append(character)
                    print(f"{character.full_name} spawns in {self.current_location.name}.")
            elif decision.type_string.lower() == "spawnitem":
                item = self.generate_item_from_prompt(decision.item)
                if item != None:
                    self.current_location.objects_in_location.append(item)
                    print(f"{item.name} spawns in {self.current_location.name}.")
            elif decision.type_string.lower() == "spawnnewlocation":
                location = self.generate_travelable_location(self.current_location, decision.location)
                if location != None:
                    self.current_location.travel_destinations.append(location)
                    print(f"{location.location} spawns in {self.current_location.name}.")
            elif decision.type_string.lower() == "modifylocationdescription":
                self.current_location.location_physical_description += "\n\n" + decision.description_addition
                print_current_screen()
            elif decision.type_string.lower() == "giveplayeritem":
                item = self.generate_item_from_prompt(decision.item)
                if item != None:
                    self.player.inventory.append(item)
                    print(f"{item.name} added to {self.player.full_name}'s inventory.")
            elif decision.type_string.lower() == "damage":
                target_character = None
                for char in self.current_location.npcs_in_location:
                    if char.full_name.lower() == decision.target_character_name.lower():
                        target_character = char
                        break
                if target_character == None:
                    if decision.target_character_name.lower() in self.player.full_name.lower():
                        target_character = self.player
                if target_character != None:
                    target_character.stats.hp -= decision.damage
                    print(f"{target_character.full_name} takes {decision.damage} damage.")
                    if target_character.stats.hp <= 0:
                        target_character.stats.hp = 0
                        print(f"{target_character.full_name} is dead.")
                        self.current_location.npcs_in_location.remove(target_character)
                        self.locations.remove(target_character)
                else:
                    if verbose:
                        print_colored(f"{decision.target_character_name} not found in location.", color="red")
            elif decision.type_string.lower() == "kill":
                target_character = None
                for char in self.current_location.npcs_in_location:
                    if char.full_name.lower() == decision.target_character_name.lower():
                        target_character = char
                        break
                if target_character == None:
                    if decision.target_character_name.lower() in self.player.full_name.lower():
                        target_character = self.player
                if target_character != None:
                    target_character.stats.hp = 0
                    print(f"{target_character.full_name} is dead.")
                    self.current_location.npcs_in_location.remove(target_character)
                    self.locations.remove(target_character)
                else:
                    if verbose:
                        print_colored(f"{decision.target_character_name} not found in location.", color="red")
            elif decision.type_string.lower() == "equip":
                target_character = None
                for char in self.current_location.npcs_in_location:
                    if char.full_name.lower() == decision.target_character_name.lower():
                        target_character = char
                        break
                if target_character == None:
                    if decision.target_character_name.lower() in self.player.full_name.lower():
                        target_character = self.player
                if target_character != None:
                    item = self.generate_item_from_prompt(decision.item)
                    if item != None:
                        if item.type_string == "Weapon":
                            target_character.equiped_weapon = item
                            print(f"{target_character.full_name} equips the {item.name}.")
                        else:
                            if item.type_string == "Headwear":
                                target_character.worn_clothing.headwear = item
                            elif item.type_string == "Upperbodywear":
                                target_character.worn_clothing.upperbodywear = item
                            elif item.type_string == "Upperbody Underwear":
                                target_character.worn_clothing.upperbody_underwear = item
                            elif item.type_string == "Fullbodywear":
                                target_character.worn_clothing.fullbodywear = item
                            elif item.type_string == "Gloves":
                                target_character.worn_clothing.gloves = item
                            elif item.type_string == "Lowerbodywear":
                                target_character.worn_clothing.lowerbodywear = item
                            elif item.type_string == "Bottom Underwear":
                                target_character.worn_clothing.bottom_underwear = item
                            elif item.type_string == "Footwear":
                                target_character.worn_clothing.footwear = item
                            elif item.type_string == "Accessory":
                                target_character.worn_clothing.accessories.append(item)
                            print(f"{target_character.full_name} equips the {item.name}.")
                    else:
                        if verbose:
                            print_colored(f"{item.name} not found.", color="red")
                else:
                    if verbose:
                        print_colored(f"{decision.target_character_name} not found in location.", color="red")
            elif decision.type_string.lower() == "unequip":
                target_character = None
                for char in self.current_location.npcs_in_location:
                    if char.full_name.lower() == decision.target_character_name.lower():
                        target_character = char
                        break
                if target_character == None:
                    if decision.target_character_name.lower() in self.player.full_name.lower():
                        target_character = self.player
                if target_character != None:
                    if decision.item == "Weapon":
                        target_character.equiped_weapon = None
                        print(f"{target_character.full_name} unequips their Weapon: {decision.item}.")
                    elif target_character.worn_clothing.headwear != None and decision.item.lower() in target_character.worn_clothing.headwear.name.lower():
                        print(f"{target_character.full_name} unequips their Headwear: {target_character.worn_clothing.headwear.name}.")
                        target_character.worn_clothing.headwear = None
                    elif target_character.worn_clothing.upperbodywear != None and decision.item.lower() in target_character.worn_clothing.upperbodywear.name.lower():
                        print(f"{target_character.full_name} unequips their Upperbodywear: {target_character.worn_clothing.upperbodywear.name}.")
                        target_character.worn_clothing.upperbodywear = None
                    elif target_character.worn_clothing.upperbody_underwear != None and decision.item.lower() in target_character.worn_clothing.upperbody_underwear.name.lower():
                        print(f"{target_character.full_name} unequips their Upperbody Underwear: {target_character.worn_clothing.upperbody_underwear.name}.")
                        target_character.worn_clothing.upperbody_underwear = None
                    elif target_character.worn_clothing.fullbodywear != None and decision.item.lower() in target_character.worn_clothing.fullbodywear.name.lower():
                        print(f"{target_character.full_name} unequips their Fullbodywear: {target_character.worn_clothing.fullbodywear.name}.")
                        target_character.worn_clothing.fullbodywear = None
                    elif target_character.worn_clothing.gloves != None and decision.item.lower() in target_character.worn_clothing.gloves.name.lower():
                        print(f"{target_character.full_name} unequips their Gloves: {target_character.worn_clothing.gloves.name}.")
                        target_character.worn_clothing.gloves = None
                    elif target_character.worn_clothing.lowerbodywear != None and decision.item.lower() in target_character.worn_clothing.lowerbodywear.name.lower():
                        print(f"{target_character.full_name} unequips their Lowerbodywear: {target_character.worn_clothing.lowerbodywear.name}.")
                        target_character.worn_clothing.lowerbodywear = None
                    elif target_character.worn_clothing.bottom_underwear != None and decision.item.lower() in target_character.worn_clothing.bottom_underwear.name.lower():
                        print(f"{target_character.full_name} unequips their Bottom Underwear: {target_character.worn_clothing.bottom_underwear.name}.")
                        target_character.worn_clothing.bottom_underwear = None
                    elif target_character.worn_clothing.footwear != None and decision.item.lower() in target_character.worn_clothing.footwear.name.lower():
                        print(f"{target_character.full_name} unequips their Footwear: {target_character.worn_clothing.footwear.name}.")
                        target_character.worn_clothing.footwear = None
                    elif target_character.worn_clothing.accessories != None:
                        for item in target_character.worn_clothing.accessories:
                            if decision.item.lower() in item.name.lower():
                                print(f"{target_character.full_name} unequips the Accessory {item.name}.")
                                target_character.worn_clothing.accessories.remove(item)
                                break
            elif decision.type_string.lower() == "drop":
                target_character = None
                for char in self.current_location.npcs_in_location:
                    if char.full_name.lower() == decision.target_character_name.lower():
                        target_character = char
                        break
                if target_character == None:
                    if decision.target_character_name.lower() in self.player.full_name.lower():
                        target_character = self.player
                if target_character != None:
                    item = self.generate_item_from_prompt(decision.item)
                    if item != None:
                        target_character.inventory.remove(item)
                        self.current_location.objects_in_location.append(item)
                        print(f"{target_character.full_name} drops the {item.name}.")
                    else:
                        if verbose:
                            print_colored(f"{item.name} not found.", color="red")
                else:
                    if verbose:
                        print_colored(f"{decision.target_character_name} not found in location.", color="red")
            elif decision.type_string.lower() == "pickup":
                target_character = None
                for char in self.current_location.npcs_in_location:
                    if char.full_name.lower() == decision.target_character_name.lower():
                        target_character = char
                        break
                if target_character == None:
                    if decision.target_character_name.lower() in self.player.full_name.lower():
                        target_character = self.player
                if target_character != None:
                    item = self.generate_item_from_prompt(decision.item)
                    if item != None:
                        target_character.inventory.append(item)
                        self.current_location.objects_in_location.remove(item)
                        print(f"{target_character.full_name} picks up the {item.name}.")
                    else:
                        if verbose:
                            print_colored(f"{item.name} not found.", color="red")
                else:
                    if verbose:
                        print_colored(f"{decision.target_character_name} not found in location.", color="red")

    def save_game(self, file_name:str):
        game_json = {
            "story_id": self.story_id,
            "story_vibe": self.story_vibe,
            "story_aesthetic": self.story_aesthetic,
            "travel_order": [loc.id for loc in self.travel_order],
            "starting_location": self.starting_location.id,
            "current_location": self.current_location.id,
            "locations": [json.loads(loc.model_dump_json()) for loc in self.locations],
            "player": json.loads(self.player.model_dump_json())
        }
        if not os.path.exists("./saves"):
            os.makedirs("./saves")
        with open("./saves/"+file_name+".json", "w", encoding="utf-8") as f:
            f.write(json.dumps(game_json, indent=4))
        # print(f"Game saved to {file_name}")
        print_colored(f"Game saved to {file_name}", color="green")

    def load_game(self, file_name:str):
        with open("./saves/"+file_name+".json", "r", encoding="utf-8") as f:
            game_json = json.loads(f.read())
        if type(game_json["locations"]) == str:
            game_json["locations"] = json.loads(game_json["locations"])
        if type(game_json["player"]) == str:
            game_json["player"] = json.loads(game_json["player"])
        if "story_id" not in game_json or game_json["story_id"] == None:
            game_json["story_id"] = generate_id()
        self.story_id = game_json["story_id"]
        self.story_vibe = game_json["story_vibe"]
        self.story_aesthetic = game_json["story_aesthetic"]
        self.locations = []
        for loc in game_json["locations"]:
            loc = Location(**loc)
            for character in loc.npcs_in_location:
                character = self.postprocess_character(character)
            self.locations.append(loc)
        self.travel_order = []
        for loc_id in game_json["travel_order"]:
            loca = None
            for loc in self.locations:
                if loc.id == loc_id:
                    loca = loc
                    break
            self.travel_order.append(loca)
        starting_loc = None
        current_loc = None
        for loc in self.locations:
            if loc.id == game_json["starting_location"]:
                starting_loc = loc
            if loc.id == game_json["current_location"]:
                current_loc = loc
            if starting_loc != None and current_loc != None:
                break
        self.starting_location = starting_loc
        self.current_location = current_loc

        self.player = Character(**game_json["player"])
        # print(f"Game loaded from {file_name}")
        print_colored(f"Game loaded from {file_name}", color="green")

    def reset_story(self):
        self.story_id = generate_id()
        self.current_location = self.starting_location
        self.travel_order = []
        # print("Story reset.")
        print_colored("Story reset.", color="red")

    def reset_id(self):
        self.story_id = generate_id()
        self.travel_order = []
        print_colored("Story ID reset.", color="red")
        
    def player_travel(self, location_name:Union[str,Location]):
        if type(location_name) == str:
            location_found = False
            last_location_name = self.current_location.name
            for t_location in self.current_location.travel_destinations:
                if location_name.lower() in t_location.portal.lower() or location_name.lower() in t_location.location_name.lower():
                    self.travel_to_location(t_location)
                    location_found = True
                    break
        else:
            self.travel_to_location(location_name)
            location_found = True
        if not location_found:
            print(f"Travelable location not found: {location_name}\nGenerating new location...")
            travelable_location = self.generate_travelable_location(self.current_location, location_name)
            self.current_location.travel_destinations.append(travelable_location)
            self.travel_to_location(travelable_location)
        if last_location_name != self.current_location.name:
            print_current_screen()

    def npc_travel(self, character, travelable_location: TravelableLocation):
        next_location = None
        for loc in self.locations:
            if loc.name == travelable_location.location_name:
                next_location = loc
                break
        if next_location == None: # location doesn't exist yet
            if verbose:
                print_colored("Location doesn't exist yet, generating...", color="green")
            print_colored(f"{character.full_name} is travelling to '"+travelable_location.location_name+"'...", color="green")
            next_location = self.generate_location_from_travelable_location(travelable_location) # generate the location
            next_location.name = travelable_location.location_name
            self.locations.append(next_location)
        can_travel = False
        for t_location in self.current_location.travel_destinations:
            if t_location.portal == travelable_location.portal:
                can_travel = True
                break
        if can_travel:
            already_has_between_location = False
            for travelable_l in next_location.travel_destinations:
                if travelable_l.location_name == self.current_location.name:
                    # print("Already has a travelable location between",previous_location.name,"and",location.name)
                    already_has_between_location = True
                    break
            if not already_has_between_location: 
                portal_already_exists = False
                while not portal_already_exists:
                    between_location = self.generate_travelable_location_between(next_location, self.current_location, travelable_location.movement_description) # generate the travelable location for coming back
                    for t_location in self.current_location.travel_destinations:
                        if t_location.portal == between_location.portal:
                            portal_already_exists = True
                            break
                    if not portal_already_exists:
                        between_location.location_name = self.current_location.name
                        next_location.travel_destinations.append(between_location)
                        portal_already_exists = True
            print(f"{character.full_name} travels to {next_location.name}.")
            # When travelling to a location, make sure you can't travel to the same location from that location
            for t_location in next_location.travel_destinations:
                if t_location.location_name == next_location.name:
                    next_location.travel_destinations.remove(t_location)
                    break
            self.current_location.npcs_in_location.remove(character)
            next_location.npcs_in_location.append(character)


def print_story(story:Story):
    print(f"{bcolors.BOLD}Story:{bcolors.ENDC}")
    print(f"Vibe: {bcolors.GREY}{story.vibe}{bcolors.ENDC}")
    print(f"Aesthetic: {bcolors.GREY}{story.aesthetic}{bcolors.ENDC}")
    print(f"Starting Location: {bcolors.GREY}{story.starting_location.name}\n{story.starting_location.location_physical_description}{bcolors.ENDC}")
    print(f"NPCs in Location: {bcolors.GREY}{len(story.starting_location.npcs_in_location)}{bcolors.ENDC}")

def print_player(player:Character):
    print(f"{bcolors.BOLD}Player Character:{bcolors.ENDC}")
    print(f"Full Name: {bcolors.GREY}{text_adventure.player.full_name}{bcolors.ENDC}")
    print(f"Nick Name: {bcolors.GREY}{text_adventure.player.nick_name}{bcolors.ENDC}")
    print(f"Age: {bcolors.GREY}{text_adventure.player.age}{bcolors.ENDC}")
    print(f"Species: {bcolors.GREY}{text_adventure.player.species}{bcolors.ENDC}")
    print(f"Race: {bcolors.GREY}{text_adventure.player.race}{bcolors.ENDC}")
    print(f"Racial Gender Term: {bcolors.GREY}{text_adventure.player.racial_gender_term}{bcolors.ENDC}")
    print(f"Gender: {bcolors.GREY}{text_adventure.player.gender}{bcolors.ENDC}")
    print(f"{text_adventure.player.full_name} - {text_adventure.player.get_physical_description()}")
    # if text_adventure.player.worn_clothing.headwear:
    #     print(f"{text_adventure.player.full_name} is wearing {text_adventure.player.worn_clothing.headwear.physical_description} on their head.")
    # if text_adventure.player.worn_clothing.fullbodywear:
    #     print(f"{text_adventure.player.full_name} is wearing {text_adventure.player.worn_clothing.fullbodywear.physical_description} on their body.")
    # if text_adventure.player.worn_clothing.upperbodywear:
    #     print(f"{text_adventure.player.full_name} is wearing {text_adventure.player.worn_clothing.upperbodywear.physical_description} on their upper body.")
    # if text_adventure.player.worn_clothing.gloves:
    #     print(f"{text_adventure.player.full_name} is wearing {text_adventure.player.worn_clothing.gloves.physical_description} on their hands.")
    # if text_adventure.player.worn_clothing.gloves:
    #     print(f"{text_adventure.player.full_name} is wearing {text_adventure.player.worn_clothing.gloves.physical_description} on their hands.")
    # if text_adventure.player.worn_clothing.lowerbodywear:
    #     print(f"{text_adventure.player.full_name} is wearing {text_adventure.player.worn_clothing.lowerbodywear.physical_description} on their lower body.")
    # if text_adventure.player.worn_clothing.footwear:
    #     print(f"{text_adventure.player.full_name} is wearing {text_adventure.player.worn_clothing.footwear.physical_description} on their feet.")
    # if text_adventure.player.equiped_weapon:
    #     print(f"{text_adventure.player.full_name} is holding {text_adventure.player.equiped_weapon.physical_description}.")

    


text_adventure = TextAIventureEngine()
text_adventure.temp = temp
text_adventure.top_p = top_p
text_adventure.min_p = min_p
text_adventure.max_tokens = max_tokens


load_game = input("Would you like to load a game? (y to load): ") == "y"
if load_game:
    save_name = input("Enter the name of the game to load: ")
    text_adventure.load_game(save_name)
    # print(f"Welcome back {text_adventure.player.full_name}!")
    print_colored(f"Welcome back {text_adventure.player.full_name}!", color="green")
else:
    use_character_card_as_starting_point = input("Would you like to use a character card as a starting point? (y to use): ") == "y"
    if use_character_card_as_starting_point:
        character_card = input("Enter the character card JSON path: ")
        character_card = json.loads(open(character_card,"r",encoding="utf-8").read())
        character_card = CharacterCard(**character_card["data"])
        # generate a story from the character card
        ready = False
        while not ready:
            story = text_adventure.generate_story_from_character_card(character_card)
            print_story(story)
            confirmation = input("Would you like to use this story? (y to confirm): ")
            if confirmation.lower() == "y":
                text_adventure.set_story(story)
                ready = True
        # generate a character from the character card for the player

        happy_with_generated_character = False
        edit_character = False
        while not happy_with_generated_character:
            print("Generating player character...")
            player_prompt = input("Enter a prompt for your character: ")
            text_adventure.player = text_adventure.generate_character_from_character_card(character_card, player_prompt, user=True)
            print_player(text_adventure.player)
            player_response = input("Are you happy with this character? (y to confirm, hit Enter to try again or type 'edit' to edit the character): ")
            if player_response.lower() == "edit" or player_response.lower() == "e":
                happy_with_generated_character = True
                edit_character = True
            else:
                happy_with_generated_character = player_response.lower() == "y"

        if edit_character:
            player_name = input("Enter the name of your character: ")
            text_adventure.player.full_name = player_name
            player_age = input("Enter the age of your character: ")
            text_adventure.player.age = int(player_age)
            player_race = input("Enter the race of your character: ")
            text_adventure.player.race = player_race
            print("Can't edit the rest of the character! (For now, alpha limitation)")
    else:
        ready = False
        while not ready:
            prompt = input("Enter a prompt for the story generation: ")
            story = text_adventure.generate_story(prompt)
            if verbose:
                print("Generated Story:",story)
            print_story(story)
            confirmation = input("Would you like to use this story? (y to confirm): ")
            if confirmation.lower() == "y":
                text_adventure.set_story(story)
                ready = True
            

        player_prompt = input("Enter a prompt for your character: ")

        happy_with_generated_character = False
        edit_character = False
        while not happy_with_generated_character:
            print("Generating player character...")
            text_adventure.player = text_adventure.generate_character_from_prompt(player_prompt)
            print_player(text_adventure.player)
            player_response = input("Are you happy with this character? (y to confirm, hit Enter to try again, type 'prompt' to enter a new prompt, or type 'edit' to edit the character): ")
            if player_response.lower() == "prompt" or player_response.lower() == "p" or player_response.lower() == "back" or player_response.lower() == "b":
                player_prompt = input("Enter a new prompt for your character: ")
            elif player_response.lower() == "edit" or player_response.lower() == "e":
                happy_with_generated_character = True
                edit_character = True
            else:
                happy_with_generated_character = player_response.lower() == "y"

        if edit_character:
            player_name = input("Enter the name of your character: ")
            text_adventure.player.full_name = player_name
            player_age = input("Enter the age of your character: ")
            text_adventure.player.age = int(player_age)
            player_race = input("Enter the race of your character: ")
            text_adventure.player.race = player_race
            print("Can't edit the rest of the character!")

    # print("SPECIAL Attributes:")
    print_colored("SPECIAL Attributes:", color="yellow")
    # print(f"Strength: {str(text_adventure.player.special_attributes.strength)}")
    # print(f"Perception: {str(text_adventure.player.special_attributes.perception)}")
    # print(f"Endurance: {str(text_adventure.player.special_attributes.endurance)}")
    # print(f"Charisma: {str(text_adventure.player.special_attributes.charisma)}")
    # print(f"Intelligence: {str(text_adventure.player.special_attributes.intelligence)}")
    # print(f"Agility: {str(text_adventure.player.special_attributes.agility)}")
    # print(f"Luck: {str(text_adventure.player.special_attributes.luck)}")
    print_colored(f"Strength: {str(text_adventure.player.special_attributes.strength)}", color="red")
    print_colored(f"Perception: {str(text_adventure.player.special_attributes.perception)}", color="grey")
    print_colored(f"Endurance: {str(text_adventure.player.special_attributes.endurance)}", color="blue")
    print_colored(f"Charisma: {str(text_adventure.player.special_attributes.charisma)}", color="yellow")
    print_colored(f"Intelligence: {str(text_adventure.player.special_attributes.intelligence)}", color="green")
    print_colored(f"Agility: {str(text_adventure.player.special_attributes.agility)}", color="cyan")
    print_colored(f"Luck: {str(text_adventure.player.special_attributes.luck)}", color="magenta")

    change_special = input("Would you like to change your SPECIAL attributes? (y to change): ") == "y"

    if change_special:
        special_order = ["STR","PER","END","CHA","INT","AGI","LCK"]
        special_index = 0
        for stat in text_adventure.player.special_attributes:
            stat_name = special_order[special_index]
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
            stat = stat_value
            special_index += 1
        print("Updated SPECIAL Attributes:")
        print(f"Strength: {str(text_adventure.player.special_attributes.strength)}")
        print(f"Perception: {str(text_adventure.player.special_attributes.perception)}")
        print(f"Endurance: {str(text_adventure.player.special_attributes.endurance)}")
        print(f"Charisma: {str(text_adventure.player.special_attributes.charisma)}")
        print(f"Intelligence: {str(text_adventure.player.special_attributes.intelligence)}")
        print(f"Agility: {str(text_adventure.player.special_attributes.agility)}")
        print(f"Luck: {str(text_adventure.player.special_attributes.luck)}")
first_turn = True # Maybe not on load?
        
def get_current_screen():
    description = f"You're currently in {text_adventure.current_location.name}.\n\n{text_adventure.current_location.location_physical_description}\n\n"
    if len(text_adventure.current_location.npcs_in_location) > 0:
        # description += "There are people here:\n"
        for character in text_adventure.current_location.npcs_in_location:
            if character in text_adventure.met:
                description += f"{bcolors.GREY}{character.full_name} is here. {character.get_equipment_description()}{bcolors.ENDC} "
                if character.stats.hp <= 0:
                    description += f"{bcolors.RED}{character.full_name} is dead.{bcolors.ENDC} "
                description = description.strip()
                description += "\n"
            else:
                description += f"{bcolors.GREY}There is{bcolors.ENDC} {character.get_unknown_description()}{bcolors.GREY}. {character.get_equipment_description()}{bcolors.ENDC} "
                if character.stats.hp <= 0:
                    description += f"{bcolors.RED}{character.get_pronouns()['subject'].capitalize()} is dead.{bcolors.ENDC} "
                description = description.strip()
                description += "\n"
    description = description.strip()
    if len(text_adventure.current_location.objects_in_location) > 0:
        # description += f"\n{bcolors.GREY}====================================={bcolors.ENDC}\n"
        # description += "\n\nItems:\n"
        description += "\n\n"
        for item in text_adventure.current_location.objects_in_location:
            # position_in_location = item.position_in_location[0].lower() + item.position_in_location[1:]
            # if position_in_location[-1] != ".":
            #     position_in_location += "."
            if item.position_in_location == None or item.position_in_location == "":
                position_in_location = "on the ground"
            else:
                position_in_location = item.position_in_location
            position_in_location = f"{position_in_location[0].lower()}{position_in_location[1:]}"
            if position_in_location[-1] == ".":
                position_in_location = position_in_location[:-1]
            description += f"There's a \"{bcolors.BLUE}{item.name}{bcolors.ENDC}\" {position_in_location}.\n" # {position_in_location}
    description = description.strip()
    if len(text_adventure.current_location.travel_destinations) > 0:
        # description += f"\n{bcolors.GREY}====================================={bcolors.ENDC}\n"
        description += f"{bcolors.GREEN}\n\nTravelable Locations From Here:{bcolors.ENDC}\n"
        for location in text_adventure.current_location.travel_destinations:
            description += f"{bcolors.BLUE}{location.location_name}{bcolors.ENDC} - \"{bcolors.BLUE}{location.portal}{bcolors.ENDC}\"\n"
    return description.strip()

def print_current_screen():
    print(get_current_screen())

# print("=====================================")
print_colored("=====================================", color="grey")

# clear_console()

print_current_screen()
while True: # Main game loop
    # Player Turn
    if first_turn:
        action = input(f"What would you like to do? (type '{bcolors.BLUE}help{bcolors.ENDC}' for a list of commands){bcolors.GREY}>{bcolors.ENDC} ")
        first_turn = False
    else:
        action = input(f"{bcolors.GREY}>{bcolors.ENDC} ")
    text_adventure.player.stats.action_points = text_adventure.player.stats.max_action_points
    def wait():
        text_adventure.player.stats.action_points = 0
        print("You wait...")
    action_args = action.split(" ")
    if action.lower() == "help" or action.lower() == "h" or action.lower() == "?":
        print("Commands:")
        print("look - Look around the current location.")
        print("inspect - Inspect an item in your inventory.")
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
        print("save - Save the game.")
        print("load - Load a game.")
        print("clear - Clear the screen.")
        print("pass - Pass time.")
        print("reset_story - Reset the story. Basically keep the locations, characters, but reset their memory to square one.")
        print("reset_id - Reset the story ID.")
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
            print_player(text_adventure.player)
        else:
            item_found = False
            for item in text_adventure.current_location.objects_in_location:
                if at.lower() in item.name.lower():
                    print(f"{bcolors.BLUE}{item.name}{bcolors.ENDC} - {bcolors.GREY}{item.physical_description}{bcolors.ENDC}")
                    item_found = True
                    break
            if not item_found:
                for character in text_adventure.current_location.npcs_in_location:
                    if at.lower() in character.full_name.lower():
                        if character in text_adventure.met:
                            print(f"{bcolors.GREY}{character.get_description()}\n{character.get_physical_description()}{bcolors.ENDC}")
                        else:
                            print(f"{bcolors.GREY}There is {character.get_unknown_description()}.\n{character.get_physical_description()}{bcolors.ENDC}")
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
                for item in text_adventure.player.inventory:
                    if at.lower() in item.name.lower():
                        print(f"{bcolors.BLUE}{item.name}{bcolors.ENDC} - {bcolors.GREY}{item.physical_description}{bcolors.ENDC}")
                        item_found = True
                        break
            if not item_found:
                for item in text_adventure.current_location.objects_in_location:
                    if item.type_string.lower() == "container":
                        for container_item in item.items:
                            if at.lower() in container_item.name.lower() or at.lower() in container_item.physical_description.lower():
                                print(f"{bcolors.BLUE}{container_item.name}{bcolors.ENDC} - {bcolors.GREY}{container_item.physical_description}{bcolors.ENDC}")
                                item_found = True
                                break
            if not item_found:
                print(f"{bcolors.RED}Item or character not found in current location:{bcolors.ENDC} {bcolors.BLUE}{at}{bcolors.ENDC}")
    elif action_args[0].lower() == "travel" or action_args[0].lower() == "t" or action_args[0].lower() == "go" or action_args[0].lower() == "walk" or action_args[0].lower() == "move":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify a location to travel to.")
            continue
        travel_to = action_args[1]
        text_adventure.player_travel(travel_to)
    elif action.lower() == "inventory" or action.lower() == "i" or action.lower() == "inv":
        print(f"You have {len(text_adventure.player.inventory)} items in your inventory:")
        for item in text_adventure.player.inventory:
            print(f"{item.type_string} - {item.name} - {item.physical_description}")
            if item.type_string.lower() == "weapon":
                print(f"Damage: {item.damage}")
        if text_adventure.player.worn_clothing.headwear:
            print(f"Headwear: {text_adventure.player.worn_clothing.headwear.name} - {text_adventure.player.worn_clothing.headwear.physical_description}")
        if text_adventure.player.worn_clothing.fullbodywear:
            print(f"Full Body Wear: {text_adventure.player.worn_clothing.fullbodywear.name} - {text_adventure.player.worn_clothing.fullbodywear.physical_description}")
        if text_adventure.player.worn_clothing.upperbodywear:
            print(f"Upper Body Wear: {text_adventure.player.worn_clothing.upperbodywear.name} - {text_adventure.player.worn_clothing.upperbodywear.physical_description}")
        if text_adventure.player.worn_clothing.gloves:
            print(f"Gloves: {text_adventure.player.worn_clothing.gloves.name} - {text_adventure.player.worn_clothing.gloves.physical_description}")
        if text_adventure.player.worn_clothing.lowerbodywear:
            print(f"Lower Body Wear: {text_adventure.player.worn_clothing.lowerbodywear.name} - {text_adventure.player.worn_clothing.lowerbodywear.physical_description}")
        if text_adventure.player.worn_clothing.footwear:
            print(f"Footwear: {text_adventure.player.worn_clothing.footwear.name} - {text_adventure.player.worn_clothing.footwear.physical_description}")
        if text_adventure.player.equiped_weapon:
            print(f"Equiped Weapon: {text_adventure.player.equiped_weapon.name} - {text_adventure.player.equiped_weapon.physical_description}")
            print(f"Damage: {text_adventure.player.equiped_weapon.damage}")
        if len(text_adventure.player.worn_clothing.accessories) > 0:
            print("Accessories:")
            for item in text_adventure.player.worn_clothing.accessories:
                print(f"{item.name} - {item.physical_description}")
    elif action_args[0].lower() == "inspect" or action_args[0].lower() == "examine" or action_args[0].lower() == "i":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to inspect.")
            continue
        item_to_inspect = action_args[1]
        item_found = False
        def print_item(item):
            for key, value in item.__dict__.items():
                if key == "type_string":
                    key = "type"
                if key == "position_in_location":
                    continue
                key = key.split("_")
                key = [k.capitalize() for k in key]
                key = " ".join(key)
                print(f"{key.capitalize()}: {str(value)}")
        if text_adventure.player.worn_clothing.headwear:
            if item_to_inspect.lower() in text_adventure.player.worn_clothing.headwear.name.lower():
                for key, value in text_adventure.player.worn_clothing.headwear.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
        if text_adventure.player.worn_clothing.fullbodywear:
            if item_to_inspect.lower() in text_adventure.player.worn_clothing.fullbodywear.name.lower():
                for key, value in text_adventure.player.worn_clothing.fullbodywear.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
        if text_adventure.player.worn_clothing.upperbodywear:
            if item_to_inspect.lower() in text_adventure.player.worn_clothing.upperbodywear.name.lower():
                for key, value in text_adventure.player.worn_clothing.upperbodywear.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
        if text_adventure.player.worn_clothing.gloves:
            if item_to_inspect.lower() in text_adventure.player.worn_clothing.gloves.name.lower():
                for key, value in text_adventure.player.worn_clothing.gloves.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
        if text_adventure.player.worn_clothing.lowerbodywear:
            if item_to_inspect.lower() in text_adventure.player.worn_clothing.lowerbodywear.name.lower():
                for key, value in text_adventure.player.worn_clothing.lowerbodywear.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
        if text_adventure.player.worn_clothing.footwear:
            if item_to_inspect.lower() in text_adventure.player.worn_clothing.footwear.name.lower():
                for key, value in text_adventure.player.worn_clothing.footwear.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
        for item in text_adventure.player.worn_clothing.accessories:
            if item_to_inspect.lower() in item.name.lower():
                for key, value in item.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
                break
        if text_adventure.player.equiped_weapon:
            if item_to_inspect.lower() in text_adventure.player.equiped_weapon.name.lower():
                for key, value in text_adventure.player.equiped_weapon.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
        for item in text_adventure.player.inventory:
            if item_to_inspect.lower() in item.name.lower():
                for key, value in item.__dict__.items():
                    print(f"{key.capitalize()}: {str(value)}")
                item_found = True
                break
        if not item_found:
            for item in text_adventure.current_location.objects_in_location:
                if item_to_inspect.lower() in item.name.lower():
                    for key, value in item.__dict__.items():
                        print(f"{key.capitalize()}: {str(value)}")
                    item_found = True
                    break
        if not item_found:
            print(f"Item not found: {item_to_inspect}")
    elif action.lower() == "stats":
        print("Your stats:")
        print(f"HP: {text_adventure.player.stats.hp}")
        print(f"Hunger: {text_adventure.player.stats.hunger}")
        print(f"Thirst: {text_adventure.player.stats.thirst}")
        print("Your SPECIAL stats:")
        special_order = ["STR","PER","END","CHA","INT","AGI","LCK"]
        special_index = 0
        for stat in text_adventure.player.special_attributes:
            stat_name = special_order[special_index]
            print(f"{stat_name}: {stat}")
            special_index += 1
    elif action_args[0].lower() == "take" or action_args[0].lower() == "get" or action_args[0].lower() == "pickup":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to take.")
            continue
        item_to_take = action_args[1]
        item_found = False
        for item in text_adventure.current_location.objects_in_location:
            if item_to_take.lower() in item.name.lower():
                text_adventure.player.inventory.append(item)
                text_adventure.current_location.objects_in_location.remove(item)
                item_found = True
                print(f"You picked up the {item.name}.")
                break
            elif item.type_string.lower() == "container":
                print(f"Searching {item.name} for {item_to_take}...")
                for container_item in item.items:
                    if item_to_take.lower() in container_item.name.lower() or item_to_take.lower() in container_item.physical_description.lower():
                        text_adventure.player.inventory.append(container_item)
                        item.items.remove(container_item)
                        for location in text_adventure.locations:
                            if location.name == text_adventure.current_location.name:
                                location.objects_in_location = text_adventure.current_location.objects_in_location
                                break
                        item_found = True
                        print(f"You took the {container_item.name} from the {item.name}.")
                        text_adventure.roleplay(text_adventure.player, f"took the {container_item.name} from the {item.name}.", True)
        if not item_found:
            for character in text_adventure.current_location.npcs_in_location:
                print(f"Searching {character.full_name} for {item_to_take}...")
                if character.worn_clothing.headwear != None:
                    if item_to_take.lower() in character.worn_clothing.headwear.name.lower() or item_to_take.lower() in character.worn_clothing.headwear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            text_adventure.player.inventory.append(character.worn_clothing.headwear)
                            item_name = character.worn_clothing.headwear.name
                            character.worn_clothing.headwear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                            text_adventure.roleplay(text_adventure.player, f"took the {item_name} from {character.full_name}.", True)
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.worn_clothing.upperbodywear != None:
                    if item_to_take.lower() in character.worn_clothing.upperbodywear.name.lower() or item_to_take.lower() in character.worn_clothing.upperbodywear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            text_adventure.player.inventory.append(character.worn_clothing.upperbodywear)
                            item_name = character.worn_clothing.upperbodywear.name
                            character.worn_clothing.upperbodywear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                            text_adventure.roleplay(text_adventure.player, f"took the {item_name} from {character.full_name}.", True)
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.worn_clothing.fullbodywear != None:
                    if item_to_take.lower() in character.worn_clothing.fullbodywear.name.lower() or item_to_take.lower() in character.worn_clothing.fullbodywear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            text_adventure.player.inventory.append(character.worn_clothing.fullbodywear)
                            item_name = character.worn_clothing.fullbodywear.name
                            character.worn_clothing.fullbodywear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                            text_adventure.roleplay(text_adventure.player, f"took the {item_name} from {character.full_name}.", True)
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.worn_clothing.gloves != None:
                    if item_to_take.lower() in character.worn_clothing.gloves.name.lower() or item_to_take.lower() in character.worn_clothing.gloves.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            text_adventure.player.inventory.append(character.worn_clothing.gloves)
                            item_name = character.worn_clothing.gloves.name
                            character.worn_clothing.gloves = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.worn_clothing.lowerbodywear != None:
                    if item_to_take.lower() in character.worn_clothing.lowerbodywear.name.lower() or item_to_take.lower() in character.worn_clothing.lowerbodywear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            text_adventure.player.inventory.append(character.worn_clothing.lowerbodywear)
                            item_name = character.worn_clothing.lowerbodywear.name
                            character.worn_clothing.lowerbodywear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.worn_clothing.footwear != None:
                    if item_to_take.lower() in character.worn_clothing.footwear.name.lower() or item_to_take.lower() in character.worn_clothing.footwear.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            text_adventure.player.inventory.append(character.worn_clothing.footwear)
                            item_name = character.worn_clothing.footwear.name
                            character.worn_clothing.footwear = None
                            print(f"You took the {item_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                if character.equiped_weapon != None:
                    if item_to_take.lower() in character.equiped_weapon.name.lower() or item_to_take.lower() in character.equiped_weapon.physical_description.lower():
                        if character.stats.hp <= 0:
                            item_found = True
                            text_adventure.player.inventory.append(character.equiped_weapon)
                            weapon_name = character.equiped_weapon
                            character.equiped_weapon = None
                            print(f"You took the {weapon_name} from {character.full_name}.")
                        else:
                            item_found = True
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                        break
                for item in character.inventory:
                    if item_to_take.lower() in item.name.lower() or item_to_take.lower() in item.physical_description.lower():
                        if character.stats.hp <= 0:
                            # TODO: Ask the character if they want to give the item to the text_adventure.player
                            text_adventure.player.inventory.append(item)
                            character.inventory.remove(item)    
                            item_found = True
                            print(f"You took the {item.name} from {character.full_name}.")
                        else:
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                            item_found = True
                        break
                for item in character.worn_clothing.accessories:
                    if item_to_take.lower() in item.name.lower() or item_to_take.lower() in item.physical_description.lower():
                        if character.stats.hp <= 0:
                            text_adventure.player.inventory.append(item)
                            character.worn_clothing.accessories.remove(item)
                            item_found = True
                            print(f"You took the {item.name} from {character.full_name}.")
                        else:
                            print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                            item_found = True
                        break
        if not item_found:
            print(f"Item not found: {item_to_take}")
        else:
            # pass_time = True
            text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "drop" or action_args[0].lower() == "discard":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to drop.")
            continue
        item_to_drop = action_args[1]
        item_found = False
        for item in text_adventure.player.inventory:
            if item_to_drop.lower() in item.name.lower() or item_to_drop.lower() in item.physical_description.lower():
                text_adventure.current_location.objects_in_location.append(item)
                text_adventure.player.inventory.remove(item)
                for location in text_adventure.locations:
                    if location.name == text_adventure.current_location.name:
                        location.objects_in_location = text_adventure.current_location.objects_in_location
                        break
                item_found = True
                print(f"You dropped the {item.name}.")
                break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_drop}")
        else:
            # pass_time = True
            text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "put" or action_args[0].lower() == "placein" or action_args[0].lower() == "placeon":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to put.")
            continue
        item_to_put = action_args[1]
        item_found = None
        for item in text_adventure.player.inventory:
            if item_to_put.lower() in item.name.lower():
                inventory_found = item
                break
        if inventory_found == None:
            print(f"Item not found in your inventory: {item_to_put}")
            continue
        where_to_put = input("Where would you like to put the item?> ")
        for item in text_adventure.current_location.objects_in_location:
            if where_to_put.lower() in item.name.lower():
                item.items.append(inventory_found)
                text_adventure.player.inventory.remove(inventory_found)
                for location in text_adventure.locations:
                    if location.name == text_adventure.current_location.name:
                        location.objects_in_location = text_adventure.current_location.objects_in_location
                        break
                item_found = True
                print(f"You put the {inventory_found.name} in the {item.name}.")
                break
        if not item_found:
            print(f"Item not found in current location: {where_to_put}")
        else:
            # pass_time = True
            text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "equip" or action_args[0].lower() == "wear":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to equip.")
            continue
        item_to_equip = action_args[1]
        item_found = False
        for item in text_adventure.player.inventory:
            if item_to_equip.lower() in item.name.lower() or item_to_equip.lower() in item.physical_description.lower():
                if item.type_string.lower() == "weapon":
                    text_adventure.player.equiped_weapon = item
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "headwear":
                    text_adventure.player.worn_clothing.headwear = item
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "upperbodywear":
                    text_adventure.player.worn_clothing.upperbodywear = item
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "lowerbodywear":
                    text_adventure.player.worn_clothing.lowerbodywear = item
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "footwear":
                    text_adventure.player.worn_clothing.footwear = item
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "gloves":
                    text_adventure.player.worn_clothing.gloves = item
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
                elif item.type_string.lower() == "accessory":
                    text_adventure.player.worn_clothing.accessories.append(item)
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You equipped the {item.name}.")
                    break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_equip}")
        else:
            # pass_time = True
            text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "unequip" or action_args[0].lower() == "remove":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to unequip.")
            continue
        item_to_unequip = action_args[1]
        item_found = False
        if text_adventure.player.equiped_weapon != None:
            if item_to_unequip.lower() in text_adventure.player.equiped_weapon.name.lower() or item_to_unequip.lower() in text_adventure.player.equiped_weapon.physical_description.lower():
                text_adventure.player.inventory.append(text_adventure.player.equiped_weapon)
                text_adventure.player.equiped_weapon = None
                item_found = True
                print(f"You unequipped the {item_to_unequip}.")
        if text_adventure.player.worn_clothing.headwear != None:
            if item_to_unequip.lower() in text_adventure.player.worn_clothing.headwear.name.lower() or item_to_unequip.lower() in text_adventure.player.worn_clothing.headwear.physical_description.lower():
                text_adventure.player.inventory.append(text_adventure.player.worn_clothing.headwear)
                text_adventure.player.worn_clothing.headwear = None
                item_found = True
                print(f"You unequipped the {item_to_unequip}.")
        if text_adventure.player.worn_clothing.upperbodywear != None:
            if item_to_unequip.lower() in text_adventure.player.worn_clothing.upperbodywear.name.lower() or item_to_unequip.lower() in text_adventure.player.worn_clothing.upperbodywear.physical_description.lower():
                text_adventure.player.inventory.append(text_adventure.player.worn_clothing.upperbodywear)
                text_adventure.player.worn_clothing.upperbodywear = None
                item_found = True
                print(f"You unequipped the {item_to_unequip}.")
        if text_adventure.player.worn_clothing.fullbodywear != None:
            if item_to_unequip.lower() in text_adventure.player.worn_clothing.fullbodywear.name.lower() or item_to_unequip.lower() in text_adventure.player.worn_clothing.fullbodywear.physical_description.lower():
                text_adventure.player.inventory.append(text_adventure.player.worn_clothing.fullbodywear)
                text_adventure.player.worn_clothing.fullbodywear = None
                item_found = True
                print(f"You unequipped the {item_to_unequip}.")
        if text_adventure.player.worn_clothing.gloves != None:
            if item_to_unequip.lower() in text_adventure.player.worn_clothing.gloves.name.lower() or item_to_unequip.lower() in text_adventure.player.worn_clothing.gloves.physical_description.lower():
                text_adventure.player.inventory.append(text_adventure.player.worn_clothing.gloves)
                text_adventure.player.worn_clothing.gloves = None
                item_found = True
                print(f"You unequipped the {item_to_unequip}.")
        if text_adventure.player.worn_clothing.lowerbodywear != None:
            if item_to_unequip.lower() in text_adventure.player.worn_clothing.lowerbodywear.name.lower() or item_to_unequip.lower() in text_adventure.player.worn_clothing.lowerbodywear.physical_description.lower():
                text_adventure.player.inventory.append(text_adventure.player.worn_clothing.lowerbodywear)
                text_adventure.player.worn_clothing.lowerbodywear = None
                item_found = True
                print(f"You unequipped the {item_to_unequip}.")
        if text_adventure.player.worn_clothing.footwear != None:
            if item_to_unequip.lower() in text_adventure.player.worn_clothing.footwear.name.lower() or item_to_unequip.lower() in text_adventure.player.worn_clothing.footwear.physical_description.lower():
                text_adventure.player.inventory.append(text_adventure.player.worn_clothing.footwear)
                text_adventure.player.worn_clothing.footwear = None
                item_found = True
                print(f"You unequipped the {item_to_unequip}.")
        if len(text_adventure.player.worn_clothing.accessories) > 0:
            for item in text_adventure.player.worn_clothing.accessories:
                if item_to_unequip.lower() in item.name.lower() or item_to_unequip.lower() in item.physical_description.lower():
                    text_adventure.player.inventory.append(item)
                    text_adventure.player.worn_clothing.accessories.remove(item)
                    item_found = True
                    print(f"You unequipped the {item_to_unequip}.")
        if not item_found:
            print(f"Item not found in your equipment: {item_to_unequip}")
        else:
            pass_time = True
    elif action_args[0].lower() == "spawn_item":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to spawn.")
            continue
        item_to_spawn = action_args[1]
        # item_found = False
        # for item in text_adventure.items:
        #     if item_to_spawn.lower() in item.name.lower() or item_to_spawn.lower() in item.physical_description.lower():
        #         text_adventure.current_location.objects_in_location.append(item)
        #         item_found = True
        #         print(f"You spawned '{item.name}' in the current location.")
        #         break
        # if not item_found:
        # Generate the item
        item = text_adventure.generate_item_from_prompt(item_to_spawn)
        text_adventure.current_location.objects_in_location.append(item)
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
        #         text_adventure.current_location.npcs_in_location.append(character)
        #         character_found = True
        #         print(f"You spawned '{character.full_name}' in the current location.")
        #         break
        # if not character_found:
        # Generate the character
        character = text_adventure.generate_character_from_prompt(character_to_spawn)
        text_adventure.current_location.npcs_in_location.append(character)
        character_found = True
        print(f"You spawned '{character.full_name}' in the current location.")
    elif action_args[0].lower() == "say":
        message = action.split(" ", 1)
        if len(message) < 2:
            print("Please specify a message to say.")
            continue
        # print(f"You say: {message[1]} (This feature is not yet implemented.)")
        text_adventure.say(text_adventure.player, message[1], True)
        # pass_time = True
        text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "find" or action_args[0].lower() == "search" or action_args[0].lower() == "lookfor" or action_args[0].lower() == "searchfor" or action_args[0].lower() == "lookaround" or action_args[0].lower() == "look" and action_args[1] == "around" or action_args[0].lower() == "searcharound" or action_args[0].lower() == "search" and action_args[1] == "around":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print_colored(f"You start looking around...","grey")
            found = text_adventure.find_item()
        else:
            to_find_prompt = action_args[1]
            print(f"{bcolors.GREY}You start looking for{bcolors.ENDC} '{bcolors.CYAN}{to_find_prompt}{bcolors.ENDC}'{bcolors.GREY}...{bcolors.ENDC}")
            found = text_adventure.find_item(to_find_prompt)
        if len(found["items"]) == 0 and len(found["characters"]) == 0 and len(found["travelable_locations"]) == 0:
            print_colored(f"You looked around but couldn't find anything new...", "red")
            continue
        else:
            found_item = False
            if verbose:
                print(f"Found:",found)
            for item in found["items"]:
                # if not already exists
                already_exists = False
                for itm in text_adventure.current_location.objects_in_location:
                    if item.name.lower() in itm.name.lower():
                        already_exists = True
                        if verbose:
                            print_colored(f"'{item.name}' already exists in the current location.", "red")
                        break
                if not already_exists:
                    text_adventure.current_location.objects_in_location.append(item)
                    found_item = True
                    print(f"You found '{bcolors.BLUE}{item.name}{bcolors.ENDC}' in the current location.")
            for character in found["characters"]:
                # if not already exists
                already_exists = False
                for char in text_adventure.current_location.npcs_in_location:
                    if character.full_name.lower() in char.full_name.lower():
                        already_exists = True
                        if verbose:
                            print_colored(f"'{character.full_name}' already exists in the current location.", "red")
                        break
                if not already_exists:
                    text_adventure.current_location.npcs_in_location.append(character)
                    found_item = True
                    print(f"You found '{bcolors.BLUE}{character.get_unknown_description()}{bcolors.ENDC}' in the current location.")
            for travelable_location in found["travelable_locations"]:
                # if not already exists
                already_exists = False
                for travelable_loc in text_adventure.current_location.travel_destinations:
                    if travelable_location.location_name.lower() in travelable_loc.location_name.lower():
                        already_exists = True
                        if verbose:
                            print_colored(f"'{travelable_location.location_name}' already exists in the current location.", "red")
                        break
                if not already_exists:
                    text_adventure.current_location.travel_destinations.append(travelable_location)
                    found_item = True
                    print(f"You found '{bcolors.BLUE}{travelable_location.location_name}{bcolors.ENDC}' in the current location.")
        if verbose:
            # print(f"You found {len(found['items'])} items, {len(found['characters'])} characters and {len(found['travelable_locations'])} travelable locations.")
            print_colored(f"You found {len(found['items'])} items, {len(found['characters'])} characters and {len(found['travelable_locations'])} travelable locations.", "yellow")
        if found_item:
            print_current_screen()
        else:
            if to_find_prompt != None:
                print_colored(f"You looked for '{to_find_prompt}' but couldn't find anything...", "red")
            else:
                print_colored(f"You looked around but couldn't find anything...", "red")
    elif action_args[0].lower() == "me" or action_args[0].lower() == "roleplay" or action_args[0].lower() == "rp":
        message = action.split(" ", 1)
        if len(message) < 2:
            print("Please specify a message to roleplay.")
            continue
        # print(f"You say: {message[1]} (This feature is not yet implemented.)")
        text_adventure.roleplay(text_adventure.player, message[1], True)
        # pass_time = True
        text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "read":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to read.")
            continue
        item_to_read = action_args[1]
        item_found = False
        for item in text_adventure.player.inventory:
            if item_to_read.lower() in item.name.lower() or item_to_read.lower() in item.physical_description.lower():
                if item.type_string.lower() == "book":
                    print(f"You start reading '{bcolors.BLUE}{item.name}{bcolors.ENDC}'.")
                    text_adventure.roleplay(text_adventure.player, f"is reading '{item.name}'", True)

                    chapter_number = 1
                    for chapter in item.chapters:
                        print(f"Chapter {chapter_number}: {chapter.chapter_title}")
                        chapter_pgs = [pg for pg in chapter.chapter_paragraphs if pg.strip() != "" and pg != None]
                        chapter_text = "\n\n".join(chapter_pgs).strip()
                        if chapter_text.endswith(", {"):
                            chapter_text = chapter_text[:-4].strip()
                        if chapter_text.endswith(","):
                            chapter_text = chapter_text[:-1].strip()
                        print_colored(bcolors.ITALICS+chapter_text,"grey")
                        next_action = input(f"Press {bcolors.BLUE}Enter{bcolors.ENDC} to continue reading or type '{bcolors.BLUE}stop{bcolors.ENDC}' to stop reading: ")
                        if next_action.lower() == "stop":
                            break
                        chapter_number += 1
                    print(f"You finished reading '{bcolors.BLUE}{item.name}{bcolors.ENDC}'.")
                    item_found = True
                    break
        if not item_found:
            # print(f"Item not fond in your inventory: {item_to_read}")
            print_colored(f"Item not found in your inventory: {item_to_read}", "red")
        else:
            # pass_time = True
            text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "eat" or action_args[0].lower() == "consume":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to eat.")
            continue
        item_to_eat = action_args[1]
        item_found = False
        for item in text_adventure.player.inventory:
            if item_to_eat.lower() in item.name.lower() or item_to_eat.lower() in item.physical_description.lower():
                if item.type_string.lower() == "food":
                    text_adventure.player.stats.hunger += item.hunger_restored
                    text_adventure.player.stats.thirst += item.thirst_restored
                    text_adventure.player.stats.hp += item.health_restored
                    text_adventure.player.inventory.remove(item)
                    for location in text_adventure.locations:
                        if location.name == text_adventure.current_location.name:
                            location.objects_in_location = text_adventure.current_location.objects_in_location
                            break
                    item_found = True
                    print(f"You ate the {item.name}.")
                    break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_eat}")
        else:
            # pass_time = True
            text_adventure.player.stats.action_points -= 1
    elif action_args[0].lower() == "attack" or action_args[0].lower() == "fight" or action_args[0].lower() == "kill" or action_args[0].lower() == "hit" or action_args[0].lower() == "hurt" or action_args[0].lower() == "shoot" or action_args[0].lower() == "punch" or action_args[0].lower() == "stab" or action_args[0].lower() == "slash":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify a character to attack.")
            continue
        character_to_attack = action_args[1]
        character_found = False
        if text_adventure.player.equiped_weapon == None:
            print("You need a weapon equipped to attack.")
            continue
        for character in text_adventure.current_location.npcs_in_location:
            if character_to_attack.lower() in character.full_name.lower() or character_to_attack.lower() in character.get_unknown_description().lower():
                character_found = True
                character.stats.hp -= text_adventure.player.equiped_weapon.damage
                if character.stats.hp <= 0:
                    if text_adventure.player.equiped_weapon:
                        print(f"You attacked {character.full_name} with your {text_adventure.player.worn_clothing['equiped_weapon'].name} and killed them.")
                    else:
                        print(f"You attacked {character.full_name} with your bare hands and killed them.")
                else:
                    if text_adventure.player.equiped_weapon:
                        print(f"You attacked {character.full_name} with your {text_adventure.player.worn_clothing.equiped_weapon.name}.")
                    else:
                        print(f"You attacked {character.full_name} with your fists.")
        # pass_time = True
        text_adventure.player.stats.action_points -= 1
    elif action.lower() == "quit" or action.lower() == "exit" or action.lower() == "q":
        print("Quitting the game...")
        break
    elif action_args[0].lower() == "save":
        if len(action_args) < 2:
            save_name = input("Enter a name for the save file: ")
        else:
            save_name = action.split(" ", 1)[1].replace(" ", "_")
        print("Saving the game...")
        text_adventure.save_game(save_name)
        print("Game saved.")
    elif action.lower() == "load":
        save_name = input("Enter the name of the save file to load: ")
        print("Loading the game...")
        text_adventure.load_game(save_name)
        print("Game loaded.")
    elif action.lower() == "clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        print_current_screen()
    elif action.lower() == "pass":
        # pass_time = True
        wait()
    elif action.lower() == "reset_story": # Assign new random story.id
        text_adventure.reset_story()
    elif action.lower() == "reset_id":
        text_adventure.reset_id()
    else:
        # print("Invalid command. Type 'help' for a list of commands.")
        if action.strip() != "":
            text_adventure.say(text_adventure.player, action, True)
        else:
            wait()
    
    if text_adventure.player.stats.action_points == 0:
        # AI Reaction/AI Turn
        if prototype_ai_turns:
            ai_turn = text_adventure.ai_turn()
        game_master_turn = text_adventure.game_master_turn()