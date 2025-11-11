from pydantic import BaseModel, Field
from typing import Union
import json
import traceback
from openai import OpenAI
import chromadb
from chromadb.config import Settings
import os
import traceback
import time
from tqdm import tqdm

from src.utils import print_colored, generate_id, bcolors, fore_fromhex
from src.get_schema_description import get_schema_description, pydantic_to_open_router_schema
from src.story.location import Location, TravelableLocation
from src.story import Story, Prompts
from src.items import SomeItem, Item, Food, Weapon
from src.character import Character, CharacterCard
from src.character.npc_decision import ActionDecision, AttackDecision, DropDecision, EquipDecision, SayDecision, TakeDecision, UnequipDecision
from src.game_mater_decision import TeleportDecision, SpawnCharacterDecision, SpawnItemDecision, SpawnNewLocationDecision, FurtherDescribeCurrentLocationDecision, GivePlayerItemDecision, DamageDecision, KillDecision, EquipItemDecision, UnequipItemDecision, DropItemDecision, PickUpItemDecision

class AnItem(BaseModel):
    """AnItem Schema - Any item in a text adventure game. All fields are required to have a value."""
    item: Union[SomeItem]

class TextAIventureEngine():
    def __init__(self, api_key:str, api_url:str, game_state = None, openrouter_style_api:bool = False, model_name:str = "gpt-4o-open-2024-08-06", verbose:bool = False):
        self.game_state = game_state
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
        self.openrouter_style_api = openrouter_style_api
        self.model_name = model_name

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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                story_json = completion.choices[0].message.content
                if self.verbose:
                    # print(json.dumps(story_json,indent=4))
                    print_colored(completion.choices[0].message.content, color="green")
                story_json = story_json.replace('\\','')
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
                if self.verbose:
                    # print(json.dumps(story_json,indent=4))
                    print_colored("2"+json.dumps(story_json,indent=4), color="green")
                story_json["starting_location"]["id"] = generate_id()
                story_json["locations"] = [story_json["starting_location"]]
                story_json["starting_location"] = story_json["starting_location"]["id"]
                if self.verbose:
                    # print(json.dumps(story_json,indent=4))
                    print_colored("3"+json.dumps(story_json,indent=4), color="green")
                story = Story.from_json(story_json)
                story.locations.append(story.starting_location)
                for character in story.starting_location.npcs_in_location:
                    character.id = generate_id()
                    character = self.postprocess_character(character)
                    
                # story_json = json.loads(story.model_dump_json())
            except Exception as e:
                if self.verbose:
                    tb = traceback.format_exc()
                    print("Error Generating Story Starter:",e,tb,completion)
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
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
                story_json["starting_location"]["id"] = generate_id()
                story_json["locations"] = [story_json["starting_location"]]
                story_json["starting_location"] = story_json["starting_location"]["id"]
                if self.verbose:
                    # print(json.dumps(story_json,indent=4))
                    print_colored(json.dumps(story_json,indent=4), color="green")
                story = Story.from_json(story_json)
                story.starting_location.id = generate_id()
                story.locations.append(story.starting_location)
                for character in story.starting_location.npcs_in_location:
                    character.id = generate_id()
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                location = Location(**location_json)
                for character in location.npcs_in_location:
                    character.id = generate_id()
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
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
        self.locations = []
        self.story_id = story.id
        self.story_vibe = story.vibe
        self.story_aesthetic = story.aesthetic
        for character in story.starting_location.npcs_in_location:
            character = self.postprocess_character(character)
        self.starting_location = story.starting_location
        self.current_location = story.starting_location
        self.locations.append(story.starting_location)
        for location in story.locations:
            for character in location.npcs_in_location:
                character = self.postprocess_character(character)
            self.locations.append(location)
        if self.game_state != None:
            if self.game_state.current_story != None:
                self.game_state.current_story.locations.append(self.starting_location)
    
    def travel_to_location(self, travelable_location:TravelableLocation):
        print_colored("You are travelling to '"+travelable_location.location_name+"'...", color="green")
        next_location = None
        for loc in self.locations:
            if loc.name == travelable_location.location_name:
                next_location = loc
                break
        if next_location == None: # location doesn't exist yet
            if self.verbose:
                print_colored("Location doesn't exist yet, generating...", color="green")
            next_location = self.generate_location_from_travelable_location(travelable_location) # generate the location
            next_location.name = travelable_location.location_name
            self.locations.append(next_location)
            if self.game_state != None:
                if self.game_state.current_story != None:
                    self.game_state.current_story.locations.append(next_location)
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
            movement_description = travelable_location.movement_description[0].upper() + travelable_location.movement_description[1:]+"."
            print(movement_description)
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                location_json = completion.choices[0].message.content
                location_json = json.loads(location_json)
                if self.verbose:
                    # print(json.dumps(location_json,indent=4))
                    print_colored(json.dumps(location_json,indent=4), color="green")
                location = Location(**location_json)
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
        if self.current_location != None:
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                character_json = completion.choices[0].message.content
                character_json = json.loads(character_json)
                if self.verbose:
                    print_colored(json.dumps(character_json,indent=4), color="green")
                character = Character(**character_json)
                character.id = generate_id()
                character = self.postprocess_character(character)
                # character_json = json.loads(character.model_dump_json())
                # print(json.dumps(character_json,indent=4))
            except Exception as e:
                if self.verbose:
                    # print("Error Generating Character:",e)
                    print_colored("Error Generating Character: "+e, color="red")
                    print("Retrying...")
                pass
        return character
    
    def postprocess_character(self, character:Character):
        if character.worn_clothing.headwear != None:
            if character.worn_clothing.headwear.name.lower() == "none" or character.worn_clothing.headwear.name.lower() == "null" or character.worn_clothing.headwear.name.strip() == "" or character.worn_clothing.headwear.name.lower() == "nil":
                character.worn_clothing.headwear = None
        if character.worn_clothing.upperbodywear != None:
            if character.worn_clothing.upperbodywear.name.lower() == "none" or character.worn_clothing.upperbodywear.name.lower() == "null" or character.worn_clothing.upperbodywear.name.strip() == "" or character.worn_clothing.upperbodywear.name.lower() == "nil":
                character.worn_clothing.upperbodywear = None
        if character.worn_clothing.fullbodywear != None:
            if character.worn_clothing.fullbodywear.name.lower() == "none" or character.worn_clothing.fullbodywear.name.lower() == "null" or character.worn_clothing.fullbodywear.name.strip() == "" or character.worn_clothing.fullbodywear.name.lower() == "nil":
                character.worn_clothing.fullbodywear = None
        if character.worn_clothing.upperbody_underwear != None:
            if character.worn_clothing.upperbody_underwear.name.lower() == "none" or character.worn_clothing.upperbody_underwear.name.lower() == "null" or character.worn_clothing.upperbody_underwear.name.strip() == "" or character.worn_clothing.upperbody_underwear.name.lower() == "nil":
                character.worn_clothing.upperbody_underwear = None
        if character.worn_clothing.gloves != None:
            if character.worn_clothing.gloves.name.lower() == "none" or character.worn_clothing.gloves.name.lower() == "null" or character.worn_clothing.gloves.name.strip() == "" or character.worn_clothing.gloves.name.lower() == "nil":
                character.worn_clothing.gloves = None
        if character.worn_clothing.lower_underwear != None:
            if character.worn_clothing.lower_underwear.name.lower() == "none" or character.worn_clothing.lower_underwear.name.lower() == "null" or character.worn_clothing.lower_underwear.name.strip() == "" or character.worn_clothing.lower_underwear.name.lower() == "nil":
                character.worn_clothing.lower_underwear = None
        if character.worn_clothing.lowerbodywear != None:
            if character.worn_clothing.lowerbodywear.name.lower() == "none" or character.worn_clothing.lowerbodywear.name.lower() == "null" or character.worn_clothing.lowerbodywear.name.strip() == "" or character.worn_clothing.lowerbodywear.name.lower() == "nil":
                character.worn_clothing.lowerbodywear = None
        if character.worn_clothing.footwear != None:
            if character.worn_clothing.footwear.name.lower() == "none" or character.worn_clothing.footwear.name.lower() == "null" or character.worn_clothing.footwear.name.strip() == "" or character.worn_clothing.footwear.name.lower() == "nil":
                character.worn_clothing.footwear = None
        if character.equiped_item != None:
            if character.equiped_item.name.lower() == "none" or character.equiped_item.name.lower() == "null" or character.equiped_item.name.strip() == "" or character.equiped_item.name.lower() == "nil":
                character.equiped_item = None
        if character.worn_clothing.accessories != None:
            for item in character.worn_clothing.accessories:
                if item.name.lower() == "none" or item.name.lower() == "null" or item.name.strip() == "" or item.name.lower() == "nil":
                    character.worn_clothing.accessories.remove(item)
        for item in character.inventory:
            if item.name.lower() == "none" or item.name.lower() == "null" or item.name.strip() == "" or item.name.lower() == "nil":
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
        if self.current_location != None:
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
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
                character.id = generate_id()
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
        schema = AnItem.model_json_schema()
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
                        },
                        max_tokens=self.max_tokens,
                        timeout=60*60
                    )
                item_json = completion.choices[0].message.content
                item_json = json.loads(item_json)
                item = AnItem(**item_json)
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
            
    def get_current_screen(self):
        stats_block = f"HP: {self.player.stats.hp}/{self.player.stats.max_hp} | AP: {self.player.stats.action_points}/{self.player.stats.max_action_points} | Level: {self.player.stats.level} | EXP: {self.player.stats.experience}/{self.player.stats.experience_to_next_level}"
        description = f"You're currently in {self.current_location.name}.\n\n{self.current_location.location_physical_description}\n\n"
        if len(self.current_location.npcs_in_location) > 0:
            # description += "There are people here:\n"
            for character in self.current_location.npcs_in_location:
                if character in self.met:
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
        if len(self.current_location.objects_in_location) > 0:
            # description += f"\n{bcolors.GREY}====================================={bcolors.ENDC}\n"
            # description += "\n\nItems:\n"
            description += "\n\n"
            for item in self.current_location.objects_in_location:
                # position_in_location = item.position_in_location[0].lower() + item.position_in_location[1:]
                # if position_in_location[-1] != ".":
                #     position_in_location += "."
                position_in_location = "here"
                # if item.position_in_location == None or item.position_in_location == "":
                #     position_in_location = "on the ground"
                # else:
                #     position_in_location = item.position_in_location
                position_in_location = f"{position_in_location[0].lower()}{position_in_location[1:]}"
                if position_in_location[-1] == ".":
                    position_in_location = position_in_location[:-1]
                description += f"There's a \"{bcolors.BLUE}{item.name}{bcolors.ENDC}\" {position_in_location}.\n" # {position_in_location}
        description = description.strip()
        if len(self.current_location.travel_destinations) > 0:
            # description += f"\n{bcolors.GREY}====================================={bcolors.ENDC}\n"
            description += f"{bcolors.GREEN}\n\nTravelable Locations From Here:{bcolors.ENDC}\n"
            for location in self.current_location.travel_destinations:
                description += f"{bcolors.BLUE}{location.location_name}{bcolors.ENDC} - \"{bcolors.BLUE}{location.portal}{bcolors.ENDC}\"\n"
        return stats_block, description.strip()

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
        some_item_schema = AnItem.model_json_schema()
        some_item_schema["additionalProperties"] = False
        some_item_schema_description = get_schema_description(some_item_schema)
        messages.append({
            "role": "system",
            "content": some_item_schema_description
        })
        prompts_schema = Prompts.model_json_schema()
        prompts_schema["additionalProperties"] = False
        prompts_schema_description = get_schema_description(prompts_schema)
        self.get_current_screen()
        # add location description
        stats_block, description = self.get_current_screen()
        messages.append({
            "role": "system",
            "content": description
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": prompts_schema
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
                    item: AnItem = self.generate_item_from_prompt(prompt+" "+prmpt.prompt)
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
            decisions: list[Union[TravelDecision, ActionDecision, AttackDecision, DropDecision, EquipDecision, SayDecision, TakeDecision, UnequipDecision]] = Field(description="A list of decisions made by the NPC. Each decision should have a type_string, and the appropriate fields for that type of decision. All decisions made by the NPC in the text adventure game.", min_length=1)

        schema = Decisions.model_json_schema()
        schema["additionalProperties"] = False
        for schema_key in schema["$defs"]:
            if schema_key == "decisions":
                schema["$defs"][schema_key]["additionalProperties"] = False
        # if self.verbose:
            # print(json.dumps(schema,indent=4))
            # print_colored("Schema: "+json.dumps(schema,indent=4), color="green")
        schema_description = get_schema_description(schema)
        decision_types: list[Union[TravelDecision, ActionDecision, AttackDecision, DropDecision, EquipDecision, SayDecision, TakeDecision, UnequipDecision]] = [TravelDecision, ActionDecision, AttackDecision, DropDecision, EquipDecision, SayDecision, TakeDecision, UnequipDecision]
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
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
            decisions: list[Union[UserTravelDecision, TeleportDecision, SpawnCharacterDecision, SpawnItemDecision, SpawnNewLocationDecision, FurtherDescribeCurrentLocationDecision, GivePlayerItemDecision, DamageDecision, KillDecision, EquipItemDecision, UnequipItemDecision, DropItemDecision, PickUpItemDecision]] = Field(description="A list of decisions made by the game master. Each decision should have a type_string, and the appropriate fields for that type of decision. All decisions made by the game master in the text adventure game.")
        schema = GameMasterDecisions.model_json_schema()
        schema["additionalProperties"] = False
        for schema_key in schema["$defs"]:
            if schema_key == "decisions":
                schema["$defs"][schema_key]["additionalProperties"] = False
        # if self.verbose:
            # print(json.dumps(schema,indent=4))
            # print_colored("Schema: "+json.dumps(schema,indent=4), color="green")
        schema_description = get_schema_description(schema)
        decision_types: list[Union[UserTravelDecision,TeleportDecision, SpawnCharacterDecision, SpawnItemDecision, SpawnNewLocationDecision, FurtherDescribeCurrentLocationDecision, GivePlayerItemDecision, DamageDecision, KillDecision, EquipItemDecision, UnequipItemDecision, DropItemDecision, PickUpItemDecision]] = [UserTravelDecision,TeleportDecision, SpawnCharacterDecision, SpawnItemDecision, SpawnNewLocationDecision, FurtherDescribeCurrentLocationDecision, GivePlayerItemDecision, DamageDecision, KillDecision, EquipItemDecision, UnequipItemDecision, DropItemDecision, PickUpItemDecision]
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
                if self.openrouter_style_api:
                    completion = self.client.chat.completions.create(
                        model=self.model_name,
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
                        model=self.model_name,
                        messages=messages,
                        temperature=self.temp,
                        top_p=self.top_p,
                        extra_body={
                            "min_p": self.min_p,
                            "response_grammar": schema
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
                if self.verbose:
                    print_colored(f"\n{character.full_name} is taking their turn...", color="yellow")
                decisions = self.generate_decisions_for_character(character)
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
                    if self.verbose:
                        print_colored(f"{character.full_name} is trying to travel...", color="yellow")
                    self.roleplay(character, f"tries to travel to {decision.location}.",should_print=False)
                    for t_location in self.current_location.travel_destinations:
                        if decision.location.lower() in t_location.portal.lower() or decision.location.lower() in t_location.location_name.lower():
                            if self.verbose:
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
                    if character.equiped_item != None:
                        if character.equiped_item.name == decision.item:
                            character.equiped_item = None
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
                    if character.equiped_item != None:
                        if character.equiped_item.name == decision.item:
                            character.equiped_item = None
                            # print(f"{character.full_name} unequips the {decision.item}.")
                            self.roleplay(character, f"unequips the {decision.item}.")
                            break
                elif decision.type_string.lower() == "equip":
                    for item in character.inventory:
                        if decision.item.lower() in item.name.lower():
                            if item.type_string == "Weapon":
                                character.equiped_item = item
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
                                    character.worn_clothing.lower_underwear = item
                                elif item.type_string == "Footwear":
                                    character.worn_clothing.footwear = item
                                elif item.type_string == "Accessory":
                                    character.worn_clothing.accessories.append(item)
                                print(f"{character.full_name} equips the {item.name}.")
                            break
                elif decision.type_string.lower() == "unequip":
                    if decision.item == "Weapon":
                        character.equiped_item = None
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
                    elif character.worn_clothing.lower_underwear != None and decision.item.lower() in character.worn_clothing.lower_underwear.name.lower():
                        print(f"{character.full_name} unequips their Bottom Underwear: {character.worn_clothing.lower_underwear.name}.")
                        character.worn_clothing.lower_underwear = None
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
        should_refresh_screen = False
        decisions = self.generate_decisions_for_game_master()
        if self.verbose:
            # print(bcolors.GREEN,decisions,bcolors.ENDC)
            print_colored(decisions, color="green")

        for decision in decisions.decisions:
            if decision.type_string.lower() == "teleport":
                teleport_location = None
                for loc in self.locations:
                    if loc.name == decision.location:
                        teleport_location = loc
                        break
                if teleport_location == None:
                    if self.verbose:
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
                    if self.verbose:
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
                if self.verbose:
                    print_colored(f"User Travel: {decision.location}", color="yellow")
                self.player_travel(decision.location)
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
                should_refresh_screen = True
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
                        # self.locations.remove(target_character)
                        # if self.game_state != None:
                        #     self.game_state.current_story.locations.remove(target_character)
                else:
                    if self.verbose:
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
                    # self.locations.remove(target_character)
                else:
                    if self.verbose:
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
                            target_character.equiped_item = item
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
                                target_character.worn_clothing.lower_underwear = item
                            elif item.type_string == "Footwear":
                                target_character.worn_clothing.footwear = item
                            elif item.type_string == "Accessory":
                                target_character.worn_clothing.accessories.append(item)
                            print(f"{target_character.full_name} equips the {item.name}.")
                    else:
                        if self.verbose:
                            print_colored(f"{item.name} not found.", color="red")
                else:
                    if self.verbose:
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
                        target_character.equiped_item = None
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
                    elif target_character.worn_clothing.lower_underwear != None and decision.item.lower() in target_character.worn_clothing.lower_underwear.name.lower():
                        print(f"{target_character.full_name} unequips their Bottom Underwear: {target_character.worn_clothing.lower_underwear.name}.")
                        target_character.worn_clothing.lower_underwear = None
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
                        if self.verbose:
                            print_colored(f"{item.name} not found.", color="red")
                else:
                    if self.verbose:
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
                        if self.verbose:
                            print_colored(f"{item.name} not found.", color="red")
                else:
                    if self.verbose:
                        print_colored(f"{decision.target_character_name} not found in location.", color="red")
        return should_refresh_screen
    
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
            if self.game_state != None:
                self.game_state.current_story.locations.append(loc)
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
        should_refresh_screen = False
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
            should_refresh_screen = True
        return should_refresh_screen

    def npc_travel(self, character, travelable_location: TravelableLocation):
        next_location = None
        for loc in self.locations:
            if loc.name == travelable_location.location_name:
                next_location = loc
                break
        if next_location == None: # location doesn't exist yet
            if self.verbose:
                print_colored("Location doesn't exist yet, generating...", color="green")
            print_colored(f"{character.full_name} is travelling to '"+travelable_location.location_name+"'...", color="green")
            next_location = self.generate_location_from_travelable_location(travelable_location) # generate the location
            next_location.name = travelable_location.location_name
            self.locations.append(next_location)
            if self.game_state != None:
                if self.game_state.current_story != None:
                    self.game_state.current_story.locations.append(next_location)
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
