import json
from openai import OpenAI
import json
from pydantic import BaseModel,Field
from typing import Union,Annotated
import gradio as gr
import threading
from message_formatter import MessageFormatter, PromptStyle
from get_schema_description import get_schema_description
import time
from duckduckgo_search import DDGS
import random
import chromadb
from chromadb.config import Settings
import requests
import bs4
from bs4 import BeautifulSoup
import uuid
import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

default_formatter = MessageFormatter()

class SPECIALAttributes(BaseModel):
    """SPECIAL Stats for a character, 1-10"""
    strength: int = Field(..., ge=1, le=10)
    perception: int = Field(..., ge=1, le=10)
    endurance: int = Field(..., ge=1, le=10)
    charisma: int = Field(..., ge=1, le=10)
    intelligence: int = Field(..., ge=1, le=10)
    agility: int = Field(..., ge=1, le=10)
    luck: int = Field(..., ge=1, le=10)

class Stats(BaseModel):
    """Stats for a character"""
    hp: int = Field(..., ge=0, description="The character's health points. This is used for things like how much damage the character can take before dying, etc.")
    hunger: int = Field(..., ge=0, le=100, description="The character's hunger level. This is used for things like how hungry the character is, how much they need to eat, etc.")
    thirst: int = Field(..., ge=0, le=100, description="The character's thirst level. This is used for things like how thirsty the character is, how much they need to drink, etc.")

class Character(BaseModel):
    """Character Schema - No stats, just descriptions. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Personality, Appearance, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Drives are what motivates the character, and can be things like "Revenge on the bandits who killed their family" or "To find the lost city of gold". Tags are used to help search for characters, and can be things like "Elf", "Wizard", "Pirate", etc. The voice description is seperate from the other descriptions, and should be able to exist by itself without the other descriptions. It should describe how the character should sound. All descriptions should be at least a paragraph long, and the first message should be at least a sentence long, but longer is not bad. The backstory is the character's history, and should be at least a paragraph long. The current scenario is what the character is currently doing, and should be at least a sentence long. The naked body description is what the character looks like without clothes, and should be at least a paragraph long and explicitly and graphically describe the character's nude body. All fields are required to have a value."""
    full_name: str
    nick_name: str
    age: int = Field(...,gt=1)
    gender: str = Field(...,examples=["Male","Female"],pattern="^(Male|Female)$")
    race: str
    species: str
    special_attributes: SPECIALAttributes
    hex_color: str = Field(...,description="The hex color code for the character's name. Should be a 6 character hex code, without the #.",pattern="^([0-9A-Fa-f]{6})$")
    personality_description: str
    outfit_description: str = Field(...,description="A description of the character's outfit. Should be at least a paragraph long.", min_length=1)
    body_description: str = Field(...,description="A description of the character's body not including the chest or genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude body.", min_length=1)
    bare_chest_description: str = Field(...,description="A description of the character's chest without clothes. Should be at least a paragraph long and explicitly and graphically describe the character's nude chest.", min_length=1)
    genital_description: str = Field(...,description="A description of the character's genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude genitals.", min_length=1)
    butt_description: str = Field(...,description="A description of the character's butt. Should be at least a paragraph long and explicitly and graphically describe the character's nude butt.", min_length=1)
    thighs_description: str = Field(...,description="A description of the character's thighs. Should be at least a paragraph long and explicitly and graphically describe the character's nude thighs.", min_length=1)
    arms_description: str = Field(...,description="A description of the character's arms. Should be at least a paragraph long and explicitly and graphically describe the character's nude arms.", min_length=1)
    hands_description: str = Field(...,description="A description of the character's hands. Should be at least a paragraph long and explicitly and graphically describe the character's nude hands.", min_length=1)
    backstory: str = Field(...,description="A description of the character's backstory. Should be at least a paragraph long.", min_length=1)

class PlayerCharacter(BaseModel):
    """Player Character Schema - A character in a text adventure game that the player can control. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Personality, Appearance, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Drives are what motivates the character, and can be things like "Revenge on the bandits who killed their family" or "To find the lost city of gold". Tags are used to help search for characters, and can be things like "Elf", "Wizard", "Pirate", etc. The voice description is seperate from the other descriptions, and should be able to exist by itself without the other descriptions. It should describe how the character should sound. All descriptions should be at least a paragraph long, and the first message should be at least a sentence long, but longer is not bad. The backstory is the character's history, and should be at least a paragraph long. The current scenario is what the character is currently doing, and should be at least a sentence long. The naked body description is what the character looks like without clothes, and should be at least a paragraph long and explicitly and graphically describe the character's nude body. All fields are required to have a value."""
    character: Character
    stats: Stats
    
class TravelableLocation(BaseModel):
    """Travelable Location Schema - A location in a text adventure game that can be traveled to. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Setting, Atmosphere, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Tags are used to help search for locations, and can be things like "Forest", "Castle", "Desert", etc. All fields are required to have a value. These should be physically connected locations to the Location parent that they are a part of. Examples of travelable locations include doors, gates, paths, etc. that lead to other nearby locations. The manner in which the characters travel to a new location. """
    portal: str = Field(..., description="The name of the portal that leads to this location. Can be a door, a gate, a hole in the ground, an actual portal, etc. The manner in which the characters travel to the new location. ", examples=[
        "The Door to the Kitchen",
        "A small path into the forest",
        "A large set of double doors",
        "Door leading outside",
        "Door to the Bee and Barb",
        "The Front Door"
    ])
    location_name: str = Field(..., description="The name of the location. Can be a city, a forest, a mountain, a cave, etc. The name of the location.", examples=[
        "Kitchen - Your House",
        "The Forest of Shadows - East Entrance",
        "The Castle of the Mad King - Throne Room",
        "Time Square - New York City",
        "The Bee and Barb",
        "City Square - Whiterun"
    ])
    location_prompt: str = Field(..., description="A brief description of the location. Can be a city, a forest, a mountain, a cave, etc. The description of the location.", examples=[
        "A small kitchen in your house",
        "A dark and foreboding forest",
        "A grand throne room in a castle",
        "A bustling city square",
        "A cozy inn",
        "A large bustling city square in the middle of the day"
    ])

class BaseItem(BaseModel):
    """BaseItem Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc. Items can also be food or weapons, which have additional fields. Only Food Items should have a hunger restored and thirst restored value. Only Weapon Items should have a damage value and required SPECIAL stats."""
    type_string: str = Field(..., description="The type of item.", examples=[
        "Item",
        "Food",
        "Weapon"
    ], pattern="^(Item|Food|Weapon)$")
    name: str
    description: str = Field(..., description="A description of the item. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(..., description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.")
    value: int = Field(...,ge=0)
    weight: int = Field(...,ge=0)

class Item(BaseItem):
    """Item Schema - An item in a text adventure game. Items can be furniture, or small objects that characters can interact with. All fields are required to have a value. Examples of items include chairs, tables, chests, boxes, stools, cups, mugs, books, etc. Items can be interacted with, picked up, moved, etc."""
    type_string: str = Field(..., description="The type of item.", pattern="^Item$")
    name: str
    description: str = Field(..., description="A description of the item. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(..., description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
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
    type_string: str = Field(..., description="The type of item.", pattern="^Food$")
    name: str
    description: str = Field(..., description="A description of the food. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(..., description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
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
    type_string: str = Field(..., description="The type of item.", pattern="^Weapon$")
    name: str
    description: str = Field(..., description="A description of the weapon. Should be at least a sentence long.", min_length=1)
    position_in_location: str = Field(..., description="The position of the item in the location. Can be a room, a building, a city, a forest, etc. The position of the item in the location.", examples=[
        "On the gun rack",
        "On the table",
        "In the chest",
        "On the shelf",
        "Beside the sandbags",
        "On the ground"
    ])
    damage: int = Field(...,ge=1,description="The amount of damage the weapon does. Should be a number between 0 and 100, but can go higher if you want to be extra.")
    strength_required: int = Field(...,ge=1,le=10,description="The amount of strength required to wield the weapon. Should be a number between 1 and 10.")
    perception_required: int = Field(...,ge=1,le=10,description="The amount of perception required to wield the weapon. Should be a number between 1 and 10.")
    endurance_required: int = Field(...,ge=1,le=10,description="The amount of endurance required to wield the weapon. Should be a number between 1 and 10.")
    charisma_required: int = Field(...,ge=1,le=10,description="The amount of charisma required to wield the weapon. Should be a number between 1 and 10.")
    intelligence_required: int = Field(...,ge=1,le=10,description="The amount of intelligence required to wield the weapon. Should be a number between 1 and 10.")
    agility_required: int = Field(...,ge=1,le=10,description="The amount of agility required to wield the weapon. Should be a number between 1 and 10.")
    luck_required: int = Field(...,ge=1,le=10,description="The amount of luck required to wield the weapon. Should be a number between 1 and 10.")

class Location(BaseModel):
    """Location Schema - A location in a text adventure game. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Setting, Atmosphere, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Tags are used to help search for locations, and can be things like "Forest", "Castle", "Desert", etc. All fields are required to have a value."""
    name: str
    location_description: str = Field(..., description="A description of the location. Should be at least a paragraph long. MUST NOT contain any information about items or characters in the location. This should strictly be a description of the location without any storytelling involved. No talking about how the player moves, don't include plot elements or thoughts that the player is thinking, merely describe the location as detailedly as possible.", min_length=1)
    travelable_locations: list[TravelableLocation] = Field(..., description="A list of travelable locations from this location. Each travelable location should have a portal, location name, and location prompt. All possible travelable locations from this location. If this is in a section of a town for instance, it could have a travelable location to the market, the inn, the blacksmith, travelable locations out of town, travelable locations to the other parts of town, etc. Be detailed when coming up with travelable locations.", min_length=1)
    objects: list[Union[Item,Food,Weapon]] = Field(..., description="A list of objects in the location. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required SPECIAL stats. If an item is a weapon, it MUST have a damage value and required SPECIAL stats. If an item is food, it MUST have a hunger restored and thirst restored value.")

class Story(BaseModel):
    """Story Schema - A story in a text adventure game. Summarizes the vibe, aesthetic, and setting of the story. All fields are required to have a value."""
    title: str
    setting: str = Field(..., description="The setting of the story. Can be a city, a forest, a mountain, a cave, etc.")
    vibe: str = Field(..., description="The vibe of the story.")
    aesthetic: str = Field(..., description="The aesthetic of the story. Can be a genre, a theme, a style, etc. The overall feel of the story and the writing of the items, characters, and locations.")
    starting_location: Location = Field(..., description="The starting location of the story.")

class TextAIventureEngine():
    def __init__(self):
        self.story_title = None
        self.story_setting = None
        self.story_vibe = None
        self.story_aesthetic = None
        self.starting_location = None
        self.locations = []
        self.item_types = []
        self.characters = []
        self.client = OpenAI(api_key="abc123", base_url="http://localhost:8000/v1/")
        # self.chroma_path = f"./chromadb"
        # self.chroma_client = chromadb.PersistentClient(self.chroma_path,Settings(anonymized_telemetry=False))
        self.temp = 1.15
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
        messages.append({
            "role": "system",
            "content": f"{schema_description}\n\n{item_schema_description}\n\n{food_schema_description}\n\n{weapon_schema_description}"
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
                        "grammar": schema,
                        "min_p": self.min_p,
                    },
                    max_tokens=self.max_tokens
                )
                story_json = completion.choices[0].message.content
                story_json = json.loads(story_json)
                story = Story(**story_json)
                print(json.dumps(story_json,indent=4))
            except Exception as e:
                # print(e)
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
                "content": f"The previous location was {previous_location.name}.\n{previous_location.location_description}"
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
                        "grammar": schema,
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
                        "grammar": schema,
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
                "content": f"The previous location was {location.name}.\n{location.location_description}"
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
            "content": "Generate a travelable location based on the following prompt:"+prompt
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
                        "grammar": schema,
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

    def generate_travelable_location_between(self, prev_location:Location, next_location2:Location):
        print("Generating Travelable Location between:",prev_location.name,"and",next_location2.name)
        messages = [
            {
                "role": "system",
                "content": "The assistant is generating a travelable location JSON to run the text adventure game with. It will adhere to the JSON schema for a travelable location, and will be returned as a JSON object. Below is reference for the schema for a travelable location.",
            },
            {
                "role": "system",
                "content": f"The previous location was {prev_location.name}.\n{prev_location.location_description}\nThe next location is {next_location2.name}.\n{next_location2.location_description}"
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
                        "grammar": schema,
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
        self.story_title = story.title
        self.story_setting = story.setting
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
        if next_location == None:
            next_location = self.generate_location_from_travelable_location(previous_location, travelable_location)
            next_location.name = travelable_location.location_name
            already_has_between_location = False
            for travelable_l in next_location.travelable_locations:
                if travelable_l.location_name == previous_location.name:
                    # print("Already has a travelable location between",previous_location.name,"and",location.name)
                    already_has_between_location = True
                    break
            if not already_has_between_location: 
                portal_already_exists = False
                while not portal_already_exists:
                    between_location = self.generate_travelable_location_between(next_location, previous_location)
                    for t_location in previous_location.travelable_locations:
                        if t_location.portal == between_location.portal:
                            portal_already_exists = True
                            break
                    if not portal_already_exists:
                        between_location.location_name = previous_location.name
                        next_location.travelable_locations.append(between_location)
                        portal_already_exists = True
            self.locations.append(next_location)
        can_travel = False
        for t_location in previous_location.travelable_locations:
            if t_location.portal == travelable_location.portal:
                can_travel = True
                break
        if can_travel:
            print(f"Travelling to {next_location.name}...")
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
                "content": f"The previous location was {current_location.name}.\n{current_location.location_description}"
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
            "content": "Generate a location based on the following prompt:"+travelable_location.location_prompt
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
                        "grammar": schema,
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
    description = f"You're currently in {current_location.name}.\n\n{current_location.location_description}\n"
    if len(current_location.objects) > 0:
        description += "Items:\n"
        for item in current_location.objects:
            position_in_location = item.position_in_location[0].lower() + item.position_in_location[1:]
            if position_in_location[-1] != ".":
                position_in_location += "."
            description += f"There's a \"{item.name}\" {position_in_location}\n"
        description += "---------------------------------\n"
    description += "Travelable Locations From Here:\n"
    for location in current_location.travelable_locations:
        description += f"\"{location.portal}\" - {location.location_name}\n"
    
    print(description)

print("=====================================")

# clear_console()

first_turn = True
print_current_screen()
while True: # Main game loop
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
        print("eat - Eat food from your inventory.")
        print("help - Display this help message.")
        print("quit - Quit the game.")
    elif action.lower() == "look":
        print_current_screen()
    elif action_args[0].lower() == "travel":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify a location to travel to.")
            continue
        travel_to = action_args[1]
        location_found = False
        last_location_name = current_location.name
        for t_location in current_location.travelable_locations:
            if travel_to.lower() in t_location.portal.lower() or travel_to.lower() in t_location.location_name.lower() or travel_to.lower() in t_location.location_prompt.lower():
                current_location = text_adventure.travel_to_location_from(current_location, t_location)
                location_found = True
                break
        if not location_found:
            print(f"Travelable location not found: {travel_to}\nGenerating new location...")
            travelable_location = text_adventure.generate_travelable_location(current_location, travel_to)
            current_location.travelable_locations.append(travelable_location)
            current_location = text_adventure.travel_to_location_from(current_location, travelable_location)
        if last_location_name != current_location.name:
            print_current_screen()
    elif action.lower() == "inventory":
        print(f"You have {len(player['inventory'])} items in your inventory:")
        for item in player["inventory"]:
            print(f"{item.type_string} - {item.name} - {item.description}")
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
    elif action_args[0].lower() == "take":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to take.")
            continue
        item_to_take = action_args[1]
        item_found = False
        for item in current_location.objects:
            if item_to_take.lower() in item.name.lower() or item_to_take.lower() in item.description.lower():
                player["inventory"].append(item)
                current_location.objects.remove(item)
                for location in text_adventure.locations:
                    if location.name == current_location.name:
                        location.objects = current_location.objects
                        break
                item_found = True
                print(f"You took the {item.name}.")
                break
        if not item_found:
            print(f"Item not found: {item_to_take}")
    elif action_args[0].lower() == "drop":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to drop.")
            continue
        item_to_drop = action_args[1]
        item_found = False
        for item in player["inventory"]:
            if item_to_drop.lower() in item.name.lower() or item_to_drop.lower() in item.description.lower():
                current_location.objects.append(item)
                player["inventory"].remove(item)
                for location in text_adventure.locations:
                    if location.name == current_location.name:
                        location.objects = current_location.objects
                        break
                item_found = True
                print(f"You dropped the {item.name}.")
                break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_drop}")
    elif action_args[0].lower() == "eat":
        action_args = action.split(" ", 1)
        if len(action_args) < 2:
            print("Please specify an item to eat.")
            continue
        item_to_eat = action_args[1]
        item_found = False
        for item in player["inventory"]:
            if item_to_eat.lower() in item.name.lower() or item_to_eat.lower() in item.description.lower():
                if item.type_string.lower() == "food":
                    player["stats"]["hunger"] += item.hunger_restored
                    player["stats"]["thirst"] += item.thirst_restored
                    player["stats"]["hp"] += item.health_restored
                    player["inventory"].remove(item)
                    for location in text_adventure.locations:
                        if location.name == current_location.name:
                            location.objects = current_location.objects
                            break
                    item_found = True
                    print(f"You ate the {item.name}.")
                    break
        if not item_found:
            print(f"Item not found in your inventory: {item_to_eat}")
    elif action.lower() == "quit":
        print("Quitting the game...")
        break
    else:
        print("Invalid command. Type 'help' for a list of commands.")