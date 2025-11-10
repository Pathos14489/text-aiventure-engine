import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Union
from src.get_schema_description import get_schema_description, pydantic_to_open_router_schema
import chromadb
from chromadb.config import Settings
import os
import traceback
import time
from tqdm import tqdm, trange
import random
from art import tprint
from ascii_magic import AsciiArt
import random

from src.utils import print_colored, print_in_box, bcolors, format_colored_text, clear_console, print_chatbox
from src.story.text_aiventure_engine import TextAIventureEngine
from src.story import Story
from src.character import Character, CharacterCard
from src.story.location import Location
import src.items as Items

def print_story(story: Story):
    print(f"{bcolors.BOLD}Story:{bcolors.ENDC}")
    print(f"Vibe: {bcolors.GREY}{story.vibe}{bcolors.ENDC}")
    print(f"Aesthetic: {bcolors.GREY}{story.aesthetic}{bcolors.ENDC}")
    print(f"Starting Location: {bcolors.GREY}{story.starting_location.name}\n{story.starting_location.location_physical_description}{bcolors.ENDC}")
    print(f"NPCs in Location: {bcolors.GREY}{len(story.starting_location.npcs_in_location)}{bcolors.ENDC}")
    print(f"Objects in Location: {bcolors.GREY}{len(story.starting_location.objects_in_location)}{bcolors.ENDC}")

def print_player(player: Character):
    print(f"{bcolors.BOLD}Player Character:{bcolors.ENDC}")
    print(f"Full Name: {bcolors.GREY}{player.full_name}{bcolors.ENDC}")
    print(f"Nick Name: {bcolors.GREY}{player.nick_name}{bcolors.ENDC}")
    print(f"Age: {bcolors.GREY}{player.age}{bcolors.ENDC}")
    print(f"Species: {bcolors.GREY}{player.species}{bcolors.ENDC}")
    print(f"Race: {bcolors.GREY}{player.race}{bcolors.ENDC}")
    print(f"Racial Gender Term: {bcolors.GREY}{player.racial_gender_term}{bcolors.ENDC}")
    print(f"Gender: {bcolors.GREY}{player.gender}{bcolors.ENDC}")
    print(f"{player.full_name} - {player.get_physical_description()}")

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

verbose = False
prototype_ai_turns = True
prototype_ai_game_master = True
should_clear_console = False

inn_keeper = AsciiArt.from_image('jaba.png')
junk_man = AsciiArt.from_image('junkman.png')
magician = AsciiArt.from_image('magician.png')

class GameState:
    def __init__(self, save_name: str = "", api_key: str = api_key, api_url: str = api_url, model_name: str = model_name, openrouter_style_api: bool = openrouter_style_api, temp: float = temp, top_p: float = top_p, min_p: float = min_p, max_tokens: int = max_tokens, verbose: bool = False):
        self.save_name = save_name
        self.money = 0
        self.day = 1
        self.rent_interval = 7
        self.first_turn = False

        # Innkeeper and Inn Descriptions and Lines
        self.inn_keeper_description_lines = [
            "Sweat drips down his rolls of smooth, oily fatty flesh as he eyes you suspiciously.",
            "He wipes his greasy hands on his stained apron, eyeing you up and down.",
            "His beady eyes glint with a mix of greed and curiosity as he sizes you up.",
            "The innkeeper's jowls quiver slightly as he contemplates your presence in his establishment.",
        ]
        self.inn_description_lines = [
            "The air is thick with the scent of stale ale and old wood.",
            "Flickering candlelight casts dancing shadows on the worn wooden walls.",
            "The floor creaks underfoot, and the muffled sounds of distant laughter echo through the halls.",
            "A faint draft carries the scent of rain from outside, mingling with the aroma of roasting meat.",
            "The walls are adorned with faded tapestries depicting scenes of long-forgotten battles.",
        ]
        self.innkeeper_lines = [
            "Eugh... You hear to pay rent or what?",
            "Rent's due soon... You got the money or not?",
            "You planning on staying long here? I wouldn't...",
            "This place ain't free, y'know...",
            "The fuck you want now?",
            "You got any business here? No? Then get lost.",
        ]

        # Junkyard and Junkman Descriptions and Lines
        self.junkyard_description_lines = [
            "The junkyard is a chaotic maze of discarded items, from rusted vehicles to broken appliances.",
            "Piles of scrap metal glint in the dim light, casting eerie shadows across the ground.",
            "The air is thick with the smell of oil and rust, mingling with the faint scent of old wood.",
            "Scattered among the debris are remnants of forgotten technology, their purpose lost to time.",
        ]
        self.junkman_description_lines = [
            "The junkman eyes you with a mix of curiosity and suspicion, his gaunt frame hunched over a cluttered workbench.",
            "Cobwebs cling to the corners of the shack, and the junkman's pale skin seems almost translucent in the dim light.",
            "His eyes dart around nervously as he fiddles with a strange contraption, clearly wary of outsiders.",
            "The junkman's thin fingers move deftly as he sorts through a pile of assorted parts, his expression unreadable.",
        ]
        self.junkman_lines = [
            "...You got any junk for me?",
            "Heh.... hehe... ...Looking to trade something?",
            "...Got any interesting bits and pieces?",
            "...You again... ...Found anything good out there?",
            "...Anything worth selling this time?",
        ]
        self.junkman_sell_lines = [
            "...What do you want to sell?",
            "...You got any junk for me?",
            "...Heh.... hehe... ...Looking to trade something?",
            "...Got any interesting bits and pieces?",
            "...You again... ...Found anything good out there?",
            "...Anything worth selling this time?",
        ]

        # Magician and Leap Descriptions and Lines
        self.edge_of_rock_description_lines = [
            "The edge of the rock drops off into an endless void, the grey expanse stretching out as far as the eye can see.",
            "A faint mist swirls around the edge, obscuring the view of what lies beyond.",
            "The air is eerily still here, with only the occasional gust of wind disturbing the silence.",
            "You can feel a strange energy emanating from the void, as if it beckons you to step closer.",
        ]
        self.magician_description_lines = [
            "The hooded figure stands tall and mysterious, his face obscured by the shadows of his cloak.",
            "A faint aura of magic seems to emanate from the figure, hinting at powers beyond comprehension.",
            "The figure's eyes glint with an otherworldly light, reflecting the endless void around you.",
            "His presence is both unsettling and intriguing, as if he holds the key to untold adventures.",
        ]
        self.magician_lines = [
            "Leap before you look...",
            "Ready to see new places?",
            "The void awaits...",
            "Take the leap of faith...",
        ]

        self.player: Character = None

        self.stories: list[Story] = []
        self.current_story: Story = None
        self.in_world: bool = False
        self.run_game: bool = True
        
        self.verbose = verbose
        
        self.text_adventure: TextAIventureEngine = TextAIventureEngine(api_key=api_key, api_url=api_url, game_state=self, model_name=model_name, openrouter_style_api=openrouter_style_api, verbose=verbose)
        self.text_adventure.temp = temp
        self.text_adventure.top_p = top_p
        self.text_adventure.min_p = min_p
        self.text_adventure.max_tokens = max_tokens
    
    def save(self, save_name: str = None):
        if save_name is not None:
            self.save_name = save_name
        save_dir = f"./saves/{self.save_name}/"
        os.makedirs(save_dir, exist_ok=True)
        with open(f"{save_dir}game_state.json", "w", encoding="utf-8") as f:
            json.dump({
                "money": self.money,
                "day": self.day,
                "rent_interval": self.rent_interval,
                "current_story": self.current_story.id if self.current_story else None,
                "first_turn": self.first_turn,
                "in_world": self.in_world,
                "inn_keeper_description_lines": self.inn_keeper_description_lines,
                "inn_description_lines": self.inn_description_lines,
                "innkeeper_lines": self.innkeeper_lines,
                "junkyard_description_lines": self.junkyard_description_lines,
                "junkman_description_lines": self.junkman_description_lines,
                "junkman_lines": self.junkman_lines,
                "junkman_sell_lines": self.junkman_sell_lines,
                "edge_of_rock_description_lines": self.edge_of_rock_description_lines,
                "magician_description_lines": self.magician_description_lines,
                "magician_lines": self.magician_lines
            }, f, indent=4)
        with open(f"{save_dir}player.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(self.player.to_json(), indent=4))
        stories_dir = f"{save_dir}stories/"
        os.makedirs(stories_dir, exist_ok=True)
        def save_story(story: Story):
            if self.verbose:
                print_colored(f"Saving story '{story.id}'...", "GREEN")
            story_json_filename = f"{stories_dir}{story.id}/story.json"
            story_player_json_filename = f"{stories_dir}{story.id}/player.json"
            locations_dir = f"{stories_dir}{story.id}/locations/"
            os.makedirs(locations_dir, exist_ok=True)
            with open(story_json_filename, "w", encoding="utf-8") as f:
                f.write(json.dumps(story.to_json(), indent=4))
            with open(story_player_json_filename, "w", encoding="utf-8") as f:
                f.write(json.dumps(self.player.to_json(), indent=4))
            done_locations = set()
            for location in story.locations:
                if location.id in done_locations:
                    continue
                if self.verbose:
                    print_colored(f"Saving location '{location.id}'...", "GREEN")
                location_dir = f"{locations_dir}{location.id}/"
                os.makedirs(location_dir, exist_ok=True)
                with open(f"{location_dir}location.json", "w", encoding="utf-8") as f:
                    f.write(json.dumps(location.to_json(), indent=4))

                location_characters_dir = f"{location_dir}characters/"
                os.makedirs(location_characters_dir, exist_ok=True)
                for character in location.npcs_in_location:
                    if self.verbose:
                        print_colored(f"Saving character '{character.id}'...", "GREEN")
                    with open(f"{location_characters_dir}{character.id}.json", "w", encoding="utf-8") as f:
                        f.write(json.dumps(character.to_json(), indent=4))
                        
                location_objects_dir = f"{location_dir}objects/"
                os.makedirs(location_objects_dir, exist_ok=True)
                for obj in location.objects_in_location:
                    if self.verbose:
                        print_colored(f"Saving object '{obj.id}'...", "GREEN")
                    with open(f"{location_objects_dir}{obj.id}.json", "w", encoding="utf-8") as f:
                        f.write(json.dumps(obj.to_json(), indent=4))
                done_locations.add(location.id)
        save_story(self.current_story)
        for story in self.stories:
            if story.id != self.current_story.id:
                save_story(story)

    def load(self, save_name: str):
        if not os.path.exists(f"./saves/{save_name}/game_state.json"):
            print_colored("Save file not found!", "RED")
            return
        save_dir = f"./saves/{save_name}/"
        with open(f"{save_dir}game_state.json", "r", encoding="utf-8") as f:
            game_state_data = json.load(f)
            self.money = game_state_data["money"]
            self.day = game_state_data["day"]
            self.rent_interval = game_state_data["rent_interval"]
            self.first_turn = game_state_data.get("first_turn", False)
            self.in_world = game_state_data.get("in_world", False)
            self.inn_keeper_description_lines = game_state_data.get("inn_keeper_description_lines", self.inn_keeper_description_lines)
            self.inn_description_lines = game_state_data.get("inn_description_lines", self.inn_description_lines)
            self.innkeeper_lines = game_state_data.get("innkeeper_lines", self.innkeeper_lines)
            self.junkyard_description_lines = game_state_data.get("junkyard_description_lines", self.junkyard_description_lines)
            self.junkman_description_lines = game_state_data.get("junkman_description_lines", self.junkman_description_lines)
            self.junkman_lines = game_state_data.get("junkman_lines", self.junkman_lines)
            self.junkman_sell_lines = game_state_data.get("junkman_sell_lines", self.junkman_sell_lines)
            self.edge_of_rock_description_lines = game_state_data.get("edge_of_rock_description_lines", self.edge_of_rock_description_lines)
            self.magician_description_lines = game_state_data.get("magician_description_lines", self.magician_description_lines)
            self.magician_lines = game_state_data.get("magician_lines", self.magician_lines)
        with open(f"{save_dir}player.json", "r", encoding="utf-8") as f:
            player_data = json.load(f)
            self.set_player(Character.from_json(player_data))
        stories_dir = f"{save_dir}stories/"
        self.stories = []
        for story_filename in os.listdir(stories_dir):
            if story_filename.endswith("_player.json"):
                continue
            with open(f"{stories_dir}{story_filename}/story.json", "r", encoding="utf-8") as f:
                story_data = json.load(f)
            locations_dir = f"{stories_dir}{story_filename.split('.')[0]}/locations/"
            story_data["locations"] = []
            for location_dirname in os.listdir(locations_dir):
                location_dir = f"{locations_dir}{location_dirname}/"
                with open(f"{location_dir}location.json", "r", encoding="utf-8") as f:
                    location_data = json.load(f)
                    location = Location.from_json(location_data)
                location.npcs_in_location = []
                location.objects_in_location = []
                location_characters_dir = f"{location_dir}characters/"
                for character_filename in os.listdir(location_characters_dir):
                    with open(f"{location_characters_dir}{character_filename}", "r", encoding="utf-8") as f:
                        character_data = json.load(f)
                        character = Character.from_json(character_data)
                        location.npcs_in_location.append(character)
                location_objects_dir = f"{location_dir}objects/"
                for object_filename in os.listdir(location_objects_dir):
                    with open(f"{location_objects_dir}{object_filename}", "r", encoding="utf-8") as f:
                        object_data = json.load(f)
                        obj = Items.from_json(object_data)
                        location.objects_in_location.append(obj)
                if "starting_location" in story_data and story_data["starting_location"] == location.id:
                    story_data["starting_location"] = location
                story_data["locations"].append(location)
            if isinstance(story_data.get("starting_location"), str):
                story_data["starting_location"] = random.choice(story_data["locations"]) if story_data["locations"] else location
            story = Story.from_json(story_data)
            self.stories.append(story)
            if story.id == game_state_data["current_story"]:
                self.current_story = story
                self.text_adventure.set_story(story)
                self.text_adventure.current_location = story.starting_location # TODO: Remember last location in save


    @property
    def progress_line(self):
        return f"Days Since Arrival: {self.day} | Money: ${self.money} | Days Until Rent Due: {self.days_until_rent_due()}"

    def days_until_rent_due(self):
        return self.rent_interval - (self.day % self.rent_interval)

    def print_current_screen(self):
        if should_clear_console:
            clear_console()
        stats_block, description = self.text_adventure.get_current_screen()
        stats_block = stats_block + f" | {self.progress_line}"
        print_in_box(stats_block, color="yellow")
        # print_in_box(description, color="cyan")
        print(description)

    def print_hub_screen(self):
        if should_clear_console:
            clear_console()
        print_in_box(self.progress_line, color="yellow")
        print(f"You're standing on the floating rock in the endless void. Around you is the Inn at the End of Time, the Junkyard, and the Hooded Figure who offers to take you to new places.")
        print_in_box(f"Available Actions:\n- {format_colored_text('inn','red')} - Go to the Inn\n- {format_colored_text('junkyard','red')} - Go to the Junkyard\n- {format_colored_text('leap','red')} - Talk to the Hooded Figure to leap to a new location\n- {format_colored_text('save','red')} - Save your progress\n- {format_colored_text('quit','red')} - Quit the game", color="cyan")

    def inn_keeper_say(self, line: str):
        print_chatbox("Innkeeper", line, speaker_color="yellow", message_color="white", box_color="grey")

    def narrator_say(self, line: str):
        print_chatbox("Narrator", line, speaker_color="grey", message_color="white", box_color="grey")

    def junkman_say(self, line: str):
        print_chatbox("Junkman", line, speaker_color="red", message_color="white", box_color="grey")

    def magician_say(self, line: str):
        print_chatbox("Hooded Figure", line, speaker_color="magenta", message_color="white", box_color="grey")

    def open_inn_screen(self):
        while True:
            if should_clear_console:
                clear_console()
            print_in_box(self.progress_line, color="yellow")
            random_inn_description = random.choice(self.inn_description_lines)
            random_inn_keeper_description = random.choice(self.inn_keeper_description_lines)
            random_innkeeper_line = random.choice(self.innkeeper_lines)
            self.narrator_say(f"You step into the dimly lit inn lobby. {random_inn_description} {random_inn_keeper_description}")
            time.sleep(2)
            inn_keeper.to_terminal(columns=120)
            self.inn_keeper_say(random_innkeeper_line)
            print_in_box("Inn Screen - Available Actions:\n- talk - Talk to the Innkeeper\n- rent - Pay Rent ($5000) \n- change_room - Change Room ($1000)\n- enter - Enter your room\n- leave - Leave the Inn", color="cyan")

            action = input("> ").lower()
            if action == "talk":
                self.narrator_say("You approach the Innkeeper.")
                time.sleep(1)
                self.inn_keeper_say(random_innkeeper_line)
            elif action == "rent":
                self.narrator_say("You ask about renting a room.")
                time.sleep(2)
                self.inn_keeper_say("That'll be 5000 gold coins for a night.")
                time.sleep(3)
                if money >= 5000:
                    self.narrator_say(f"You pay the Innkeeper ${self.rent}... You can see his oil-y skin leaving a mark on the bills as you hand them over to him, like he's counting the bills with boiled hotdogs weiners...")
                    money -= 5000
                    time.sleep(2)
                    self.inn_keeper_say("Eugh... Thanks. You're good for another week. Now get out of my sight...")
                else:
                    self.inn_keeper_say("You don't have enough money? You better get the rest before due date... Or you're not welcome on this rock anymore.")
            elif action == "change_room":
                self.narrator_say("You ask about changing your room.")
                time.sleep(2)
                self.inn_keeper_say("That'll be 1000 gold coins to change rooms.")
                time.sleep(3)
                if money >= 1000:
                    self.narrator_say("You pay the Innkeeper $1000 to change your room... You can see his oil-y skin leaving a mark on the bills as you hand them over to him, like he's counting the bills with boiled hotdogs weiners...")
                    money -= 1000
                    time.sleep(2)
                    self.inn_keeper_say("Damn... Fine. What kinda room you want now?")
                    room_preference = input("Enter your new room preference: ")
                    self.narrator_say(f"You tell the Innkeeper you'd like a room that is {room_preference}.")
                    time.sleep(2)
                    room_number = random.randint(1, 999999999999)
                    self.inn_keeper_say(f"...Alright, got it. You're in room {room_number}. Now get the hell out of my sight.")
                else:
                    if self.money >= self.rent // 2:
                        self.inn_keeper_say(f"You don't have enough money? You better get some money before due date... You owe me in {self.days_until_rent_due()} days.")
                    else:
                        self.inn_keeper_say(f"You don't have enough money? You better get some money before due date... This isn't even half of what you owe me in {self.days_until_rent_due()} days and you're trying to change rooms? Get the fuck out of here.")
            elif action == "leave":
                self.narrator_say("You decide to leave the Inn.")
                break
            else:
                self.narrator_say("Invalid action. Please choose again.")

    def open_junkyard_screen(self):
        while True:
            if should_clear_console:
                clear_console()
            print_in_box(self.progress_line, color="yellow")
            random_junkyard_description = random.choice(self.junkyard_description_lines)
            random_junkman_description = random.choice(self.junkman_description_lines)
            random_junkman_line = random.choice(self.junkman_lines)
            self.narrator_say(f"You step into the junkyard. {random_junkyard_description} You see the junkman in his shack. {random_junkman_description}")
            time.sleep(2)
            junk_man.to_terminal(columns=90)
            self.junkman_say( random_junkman_line)
            time.sleep(2)
            print_in_box("Junkyard Screen - Available Actions:\n- talk - Talk to the Junkman\n- buy (doesn't work yet) - Buy items from the Junkman\n- sell - Sell items to the Junkman\n- leave - Leave the Junkyard", color="cyan")

            action = input("> ").lower()
            if action == "talk":
                self.narrator_say("You approach the Junkman.")
                time.sleep(1)
                self.junkman_say( random_junkman_line)
            elif action == "sell":
                self.narrator_say("You ask the Junkman about selling items.")
                time.sleep(2)
                random_junkman_sell_line = random.choice(self.junkman_sell_lines)
                self.junkman_say( random_junkman_sell_line)
                time.sleep(2)
                item_to_sell = input("Enter the item you want to sell: ")
                item_value = random.randint(100, 1000)
                self.narrator_say(f"You offer to sell the Junkman your {item_to_sell}.")
                time.sleep(2)
                self.junkman_say( f"I'll give you ${item_value} for that.")
                time.sleep(2)
                confirm_sale = input("Sell the item? y/n: ") == "y"
                if confirm_sale:
                    self.money += item_value
                    self.narrator_say(f"You sell your {item_to_sell} to the Junkman for ${item_value}.")
                else:
                    self.narrator_say("You decide not to sell the item.")
            elif action == "leave":
                self.narrator_say("You decide to leave the Junkyard.")
                break
            else:
                self.narrator_say("Invalid action. Please choose again.")
                continue

    def open_edge_of_rock_screen(self):
        while True:
            if should_clear_console:
                clear_console()
            print_in_box(self.progress_line, color="yellow")
            random_edge_description = random.choice(self.edge_of_rock_description_lines)
            random_magician_description = random.choice(self.magician_description_lines)
            random_magician_line = random.choice(self.magician_lines)
            self.narrator_say(f"You stand at the edge of the floating rock. {random_edge_description} The hooded figure stands nearby. {random_magician_description}")
            time.sleep(2)
            magician.to_terminal(columns=90)
            self.magician_say( random_magician_line)
            time.sleep(2)
            print_in_box("Edge of Rock Screen - Available Actions:\n- talk - Talk to the Hooded Figure\n- leap - Leap into the void to a new location\n- leave - Step away from the edge", color="cyan")

            action = input("> ").lower()
            if action == "talk":
                self.narrator_say("You approach the Hooded Figure.")
                time.sleep(1)
                self.magician_say( random_magician_line)
            elif action == "leap":
                self.magician_say( "Where would you like to leap to?")
                leap_destination = input(">")
                story = self.text_adventure.generate_story(leap_destination)
                if verbose:
                    print("Generated Story:",story)
                print_story(story)
                confirmation = input("Would you like to use this story? (y to confirm): ")
                if confirmation.lower() == "y":
                    self.text_adventure.set_story(story)
                    self.print_current_screen()
                    in_world = True
                    break
                self.narrator_say("You decide to leap into the void...")
                time.sleep(2)
                self.narrator_say("As you leap, a swirling vortex of colors envelops you, and you find yourself transported to a new location!")
                # Here you would implement the actual location change logic
                break
            elif action == "leave":
                self.narrator_say("You step away from the edge of the rock.")
                break
            else:
                self.narrator_say("Invalid action. Please choose again.")

    def set_player(self, player: Character):
        self.player = player
        self.text_adventure.player = player

    def opening_cutscene(self, skip_cutscene: bool = False, player_prompt: str = None, room_prompt: str = None, first_story_prompt: str = None):
        if should_clear_console:
            clear_console()
        if not skip_cutscene:
            self.narrator_say("Your story begins where everything ends... In the space between spaces at the Inn at the End of Time...")
            time.sleep(1.5)
            inn_keeper.to_terminal(columns=120)
            print_chatbox("Innkeeper","Ergh... Who're you? Why're you here?", speaker_color="yellow", message_color="red", box_color="grey")
        if player_prompt is None:
            player_prompt = input("Enter a description of your character: ")

        happy_with_generated_character = False
        edit_character = False
        while not happy_with_generated_character:
            print("Generating player character...")
            self.set_player(self.text_adventure.generate_character_from_prompt(player_prompt))
            print_player(self.player)
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
            self.player.full_name = player_name
            player_age = input("Enter the age of your character: ")
            self.player.age = int(player_age)
            player_race = input("Enter the race of your character: ")
            self.player.race = player_race
            print("Can't edit the rest of the character!")

        # print("SPECIAL Attributes:")
        print_colored("Attributes:", color="yellow")
        print_colored(f"Strength: {str(self.player.attributes.strength)}", color="red")
        print_colored(f"Perception: {str(self.player.attributes.perception)}", color="grey")
        print_colored(f"Endurance: {str(self.player.attributes.endurance)}", color="blue")
        print_colored(f"Charisma: {str(self.player.attributes.charisma)}", color="yellow")
        print_colored(f"Intelligence: {str(self.player.attributes.intelligence)}", color="green")
        print_colored(f"Agility: {str(self.player.attributes.agility)}", color="cyan")
        print_colored(f"Luck: {str(self.player.attributes.luck)}", color="magenta")

        change_special = input("Would you like to change your Attributes? (y to change): ") == "y"

        if change_special:
            special_order = ["STR","PER","END","CHA","INT","AGI","LCK"]
            special_index = 0
            for stat in self.player.attributes:
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
            print("Updated Attributes:")
            print(f"Strength: {str(self.player.attributes.strength)}")
            print(f"Perception: {str(self.player.attributes.perception)}")
            print(f"Endurance: {str(self.player.attributes.endurance)}")
            print(f"Charisma: {str(self.player.attributes.charisma)}")
            print(f"Intelligence: {str(self.player.attributes.intelligence)}")
            print(f"Agility: {str(self.player.attributes.agility)}")
            print(f"Luck: {str(self.player.attributes.luck)}")

        if not skip_cutscene:
            if should_clear_console:
                clear_console()
            inn_keeper.to_terminal(columns=120)
            print_chatbox("Innkeeper","Y'know... I don't care who you are.", speaker_color="yellow", message_color="red", box_color="grey")
            time.sleep(1.5)
            self.narrator_say("The innkeeper is a sweaty, fat, wrinkled man of sorts... you think. ...You're not sure how you got here.")
            time.sleep(1.5)
            print_chatbox("Innkeeper","If you want a room, rent's $5,000 a week. Pay it or get the fuck out of my inn.", speaker_color="yellow", message_color="red", box_color="grey")
            time.sleep(3)
            self.narrator_say("You pay your tab using almost all your money... You should've saved more.")
            input("Press Enter to continue...")

            if should_clear_console:
                clear_console()
            inn_keeper.to_terminal(columns=120)
            print_chatbox("Innkeeper","Good... Good... What kinda room you want? Customization's on the house...", speaker_color="yellow", message_color="red", box_color="grey")
        if room_prompt is None:
            room_prompt = input("Enter your room preference: ")

        room_number = random.randint(1, 999999999999)

        if not skip_cutscene:
            if should_clear_console:
                clear_console()
            inn_keeper.to_terminal(columns=120)
            print_chatbox("Innkeeper",f"\"{room_prompt}\"... Alright, got it. Now get the fuck out of my lobby, I dont't want to hear or see you again unless it's about next week's pay. You're in room {room_number}.", speaker_color="yellow", message_color="red", box_color="grey")
            time.sleep(2)
            self.narrator_say("The innkeeper slides a key over the counter with the room number attached with a string and label. You take it, but walk outside of the inn to get some air.")
            time.sleep(2)
            self.narrator_say("As you're step outside, you find that the inn is floating on a rock in an endless grey void.")
            time.sleep(2)
            self.narrator_say("A hooded figure stands near the edge with a sign beside him. It reads 'Leap before you look'. Nearby the inn is a large fenced-in yard full of junk and oddities.")
            time.sleep(2)
            self.narrator_say("You step into the junk yard and find a variety of discarded items, from broken furniture to strange mechanical parts. In the center of it all is a run down shack.")
            input("Press Enter to continue...")

            
            if should_clear_console:
                clear_console()
            junk_man.to_terminal(columns=90)
            self.narrator_say("You step into the shack and find a thin, gaunt, pale man sitting behind a counter covered in dust. Cobwebs fill every cornre of the shop, the skeletal man having a few hanging off his marble-esque features.")
            input("Press Enter to continue...")
            self.junkman_say("...")
            time.sleep(1)
            self.junkman_say("...Hey")
            time.sleep(3)
            self.junkman_say("...You've met that innkeeper, right?")
            time.sleep(2)
            self.junkman_say("...Bet he asked for a lot of money for rent...")
            time.sleep(5)
            self.junkman_say("...I like to collect junk... Maybe we can help each other...")
            input("Press Enter to continue...")
            
            if should_clear_console:
                clear_console()
            junk_man.to_terminal(columns=90)
            self.junkman_say("...You bring me junk... And I'll pay you for it... heh...")
            time.sleep(3)
            self.junkman_say("...Go out to the yard, ask around... Find some junk... Bring it back here...")
            time.sleep(3)
            self.junkman_say("...I'll be here...")
            input("Press Enter to continue...")

            
            if should_clear_console:
                clear_console()
            self.narrator_say("You step back outside into the junkyard, the hooded figure still standing by the edge of the rock. He waves you over.")
            input("Press Enter to continue...")
            magician.to_terminal(columns=90)
            self.magician_say("Ah, a new arrival... Welcome to the space between spaces.")
            time.sleep(2)
            self.magician_say("The Junkman has seen to you already, I see. A fair arrangement, if you ask me.")
            time.sleep(2)
            self.magician_say("You might find that there's no junk left here... but don't be discouraged. There are other places to explore.")
            time.sleep(2)
            self.magician_say("For a price, you can tell me where you want to go, and I'll make sure you get there when you leap off the edge.")
            time.sleep(2)
            self.magician_say("Of course, you can leap without paying but... well... let's just say the fall might be a bit more... permanent.")
            input("Press Enter to continue...")
        ready = False
        while not ready:
            if first_story_prompt is None:
                first_universe_prompt = input("Where do you want to go?: ")
            else:
                first_universe_prompt = first_story_prompt
            story = self.text_adventure.generate_story(first_universe_prompt)
            if verbose:
                print("Generated Story:",story)
            print_story(story)
            confirmation = input("Would you like to use this story? (y to confirm): ")
            if confirmation.lower() == "y":
                self.stories.append(story)
                self.current_story = story
                self.text_adventure.set_story(story)
                ready = True
                
        if not skip_cutscene:
            if should_clear_console:
                clear_console()
            magician.to_terminal(columns=90)
            self.magician_say(f"Ah... A fine choice. Prepare yourself and leap when ready...")
            time.sleep(2)
            self.narrator_say("You approach the edge of the rock, the void stretching out infinitely below you. Taking a deep breath, you leap off the edge...")
            time.sleep(2)
            self.narrator_say("As you fall, the world around you shifts and changes. Colors blur together, shapes morph and twist. After what feels like an eternity, you land with a thud on solid ground.")
            time.sleep(2)
            input("Press Enter to continue...")
        self.first_turn = True # Maybe not on load?
        self.run_game = True

    def trigger_save(self, save_name: str = None):
        if save_name is None:
            save_name = self.save_name
        print("Saving the game...")
        # game_state.text_adventure.save_game(save_name)
        game_state.save(save_name)
        print("Game saved.")

    def hub_loop(self): 
        while self.run_game: # Hub World Loop - L2
            if self.first_turn:
                self.in_world = True
            else: # Hub Screen
                if should_clear_console:
                    clear_console()
            if not self.in_world:
                self.print_hub_screen()
            while not self.in_world: # Hub Screen Loop - L2.1
                hub_action = input(f"{bcolors.GREY}>{bcolors.ENDC} ")
                hub_action_args = hub_action.split(" ")
                if hub_action.lower() == "inn":
                    self.open_inn_screen()
                elif hub_action.lower() == "junkyard":
                    self.open_junkyard_screen()
                elif hub_action.lower() == "leap":
                    self.open_edge_of_rock_screen()
                elif hub_action.lower() == "quit" or hub_action.lower() == "exit":
                    self.in_world = False
                    self.run_game = False
                    break
                elif hub_action.lower() == "save":
                    if len(hub_action_args) < 2:
                        save_name = input("Enter a name for the save file: ")
                        if save_name.strip() == "":
                            save_name = None
                    else:
                        save_name = hub_action.split(" ", 1)[1].replace(" ", "_")
                    self.trigger_save(save_name)
                else:
                    print_colored("Invalid action. Please try again.", "red")
                if should_clear_console:
                    clear_console()
            if self.in_world:
                self.print_current_screen()
            self.in_world_loop() # In-World Loop - L3

    def in_world_loop(self):
        while self.in_world:  # In-World Loop - L3
            should_refresh = False
            # Player Turn
            if self.first_turn:
                self.print_current_screen()
                action = input(f"What would you like to do? (type '{format_colored_text('help','blue')}' for a list of commands){format_colored_text('>','grey')} ")
                self.first_turn = False
            else:
                action = input(f"{format_colored_text('>','grey')} ")
            self.text_adventure.player.stats.action_points = self.text_adventure.player.stats.max_action_points
            def wait():
                self.text_adventure.player.stats.action_points = 0
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
                    self.print_current_screen()
                elif at == "me" or at == "myself":
                    print_player(game_state.text_adventure.player)
                else:
                    item_found = False
                    for item in game_state.text_adventure.current_location.objects_in_location:
                        if at.lower() in item.name.lower():
                            print(f"{bcolors.BLUE}{item.name}{bcolors.ENDC} - {bcolors.GREY}{item.physical_description}{bcolors.ENDC}")
                            item_found = True
                            break
                    if not item_found:
                        for character in game_state.text_adventure.current_location.npcs_in_location:
                            if at.lower() in character.full_name.lower():
                                if character in game_state.text_adventure.met:
                                    print(f"{bcolors.GREY}{character.get_description()}\n{character.get_physical_description()}{bcolors.ENDC}")
                                else:
                                    print(f"{bcolors.GREY}There is {character.get_unknown_description()}.\n{character.get_physical_description()}{bcolors.ENDC}")
                                item_found = True
                                break
                            elif (character not in game_state.text_adventure.met and at.lower() in character.get_unknown_description().lower()) or (character in game_state.text_adventure.met and at.lower() in character.get_description().lower()) or (at.lower() in character.get_physical_description().lower()):
                                if character in game_state.text_adventure.met:
                                    print(f"{character.get_description()}\n{character.get_physical_description()}")
                                else:
                                    print(f"There is {character.get_unknown_description()}.\n{character.get_physical_description()}")
                                item_found = True
                                break
                    if not item_found:
                        for item in game_state.text_adventure.player.inventory:
                            if at.lower() in item.name.lower():
                                print(f"{bcolors.BLUE}{item.name}{bcolors.ENDC} - {bcolors.GREY}{item.physical_description}{bcolors.ENDC}")
                                item_found = True
                                break
                    if not item_found:
                        for item in game_state.text_adventure.current_location.objects_in_location:
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
                should_refresh = game_state.text_adventure.player_travel(travel_to)
            elif action.lower() == "inventory" or action.lower() == "i" or action.lower() == "inv":
                print(f"You have {len(game_state.text_adventure.player.inventory)} items in your inventory:")
                for item in game_state.text_adventure.player.inventory:
                    print(f"{item.type_string} - {item.name} - {item.physical_description}")
                    if item.type_string.lower() == "weapon":
                        # print(f"Damage: {item.damage}")
                        print(f"Damage Range: {item.dies_to_roll}-{item.dies_to_roll * item.max_damage_per_die} ({item.dies_to_roll}d{item.max_damage_per_die})")
                if game_state.text_adventure.player.worn_clothing.headwear:
                    print(f"Headwear: {game_state.text_adventure.player.worn_clothing.headwear.name} - {game_state.text_adventure.player.worn_clothing.headwear.physical_description}")
                if game_state.text_adventure.player.worn_clothing.fullbodywear:
                    print(f"Full Body Wear: {game_state.text_adventure.player.worn_clothing.fullbodywear.name} - {game_state.text_adventure.player.worn_clothing.fullbodywear.physical_description}")
                if game_state.text_adventure.player.worn_clothing.upperbodywear:
                    print(f"Upper Body Wear: {game_state.text_adventure.player.worn_clothing.upperbodywear.name} - {game_state.text_adventure.player.worn_clothing.upperbodywear.physical_description}")
                if game_state.text_adventure.player.worn_clothing.gloves:
                    print(f"Gloves: {game_state.text_adventure.player.worn_clothing.gloves.name} - {game_state.text_adventure.player.worn_clothing.gloves.physical_description}")
                if game_state.text_adventure.player.worn_clothing.lowerbodywear:
                    print(f"Lower Body Wear: {game_state.text_adventure.player.worn_clothing.lowerbodywear.name} - {game_state.text_adventure.player.worn_clothing.lowerbodywear.physical_description}")
                if game_state.text_adventure.player.worn_clothing.footwear:
                    print(f"Footwear: {game_state.text_adventure.player.worn_clothing.footwear.name} - {game_state.text_adventure.player.worn_clothing.footwear.physical_description}")
                if game_state.text_adventure.player.equiped_item:
                    print(f"Equiped Weapon: {game_state.text_adventure.player.equiped_item.name} - {game_state.text_adventure.player.equiped_item.physical_description}")
                    # print(f"Damage: {game_state.text_adventure.player.equiped_item.damage}")
                    print(f"Damage Range: {game_state.text_adventure.player.equiped_item.dies_to_roll}-{game_state.text_adventure.player.equiped_item.dies_to_roll * game_state.text_adventure.player.equiped_item.max_damage_per_die} ({game_state.text_adventure.player.equiped_item.dies_to_roll}d{game_state.text_adventure.player.equiped_item.max_damage_per_die})")
                if len(game_state.text_adventure.player.worn_clothing.accessories) > 0:
                    print("Accessories:")
                    for item in game_state.text_adventure.player.worn_clothing.accessories:
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
                if game_state.text_adventure.player.worn_clothing.headwear:
                    if item_to_inspect.lower() in game_state.text_adventure.player.worn_clothing.headwear.name.lower():
                        for key, value in game_state.text_adventure.player.worn_clothing.headwear.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                if game_state.text_adventure.player.worn_clothing.fullbodywear:
                    if item_to_inspect.lower() in game_state.text_adventure.player.worn_clothing.fullbodywear.name.lower():
                        for key, value in game_state.text_adventure.player.worn_clothing.fullbodywear.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                if game_state.text_adventure.player.worn_clothing.upperbodywear:
                    if item_to_inspect.lower() in game_state.text_adventure.player.worn_clothing.upperbodywear.name.lower():
                        for key, value in game_state.text_adventure.player.worn_clothing.upperbodywear.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                if game_state.text_adventure.player.worn_clothing.gloves:
                    if item_to_inspect.lower() in game_state.text_adventure.player.worn_clothing.gloves.name.lower():
                        for key, value in game_state.text_adventure.player.worn_clothing.gloves.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                if game_state.text_adventure.player.worn_clothing.lowerbodywear:
                    if item_to_inspect.lower() in game_state.text_adventure.player.worn_clothing.lowerbodywear.name.lower():
                        for key, value in game_state.text_adventure.player.worn_clothing.lowerbodywear.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                if game_state.text_adventure.player.worn_clothing.footwear:
                    if item_to_inspect.lower() in game_state.text_adventure.player.worn_clothing.footwear.name.lower():
                        for key, value in game_state.text_adventure.player.worn_clothing.footwear.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                for item in game_state.text_adventure.player.worn_clothing.accessories:
                    if item_to_inspect.lower() in item.name.lower():
                        for key, value in item.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                        break
                if game_state.text_adventure.player.equiped_item:
                    if item_to_inspect.lower() in game_state.text_adventure.player.equiped_item.name.lower():
                        for key, value in game_state.text_adventure.player.equiped_item.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                for item in game_state.text_adventure.player.inventory:
                    if item_to_inspect.lower() in item.name.lower():
                        for key, value in item.__dict__.items():
                            print(f"{key.capitalize()}: {str(value)}")
                        item_found = True
                        break
                if not item_found:
                    for item in game_state.text_adventure.current_location.objects_in_location:
                        if item_to_inspect.lower() in item.name.lower():
                            for key, value in item.__dict__.items():
                                print(f"{key.capitalize()}: {str(value)}")
                            item_found = True
                            break
                if not item_found:
                    print(f"Item not found: {item_to_inspect}")
            elif action.lower() == "stats":
                # print("Your stats:")
                # print(f"HP: {game_state.text_adventure.player.stats.hp}")
                # print(f"Hunger: {game_state.text_adventure.player.stats.hunger}")
                # print(f"Thirst: {game_state.text_adventure.player.stats.thirst}")
                # print("Your Attributes:")
                # special_order = ["STR","PER","END","CHA","INT","AGI","LCK"]
                # special_index = 0
                # for stat in game_state.text_adventure.player.attributes:
                #     stat_name = special_order[special_index]
                #     print(f"{stat_name}: {stat}")
                #     special_index += 1
                stat_block = ""
                stat_block += format_colored_text("Your stats:", color="yellow") + "\n"
                stat_block += format_colored_text(f"HP: {game_state.text_adventure.player.stats.hp}/{game_state.text_adventure.player.stats.max_hp}", color="red") + " | "
                stat_block += format_colored_text(f"Hunger: {game_state.text_adventure.player.stats.hunger}/100", color="green") + " | "
                stat_block += format_colored_text(f"Thirst: {game_state.text_adventure.player.stats.thirst}/100", color="blue") + " | "
                stat_block += format_colored_text(f"Fatigue: {game_state.text_adventure.player.stats.fatigue}/100", color="cyan") + "\n"
                stat_block += format_colored_text("Attributes:", color="yellow") + "  " + format_colored_text("Magical Attributes:", color="yellow") + "\n"
                attribute_colors = {
                    "strength": "red",
                    "perception": "green",
                    "endurance": "blue",
                    "charisma": "yellow",
                    "intelligence": "purple",
                    "agility": "cyan",
                    "luck": "magenta"
                }
                attribute_order = ["STR","PER","END","CHA","INT","AGI","LCK"]
                magical_attribute_colors = {
                    "power": "red",
                    "precision": "green",
                    "fortitude": "blue",
                    "flourish": "yellow",
                    "willpower": "purple",
                    "multitasking": "cyan",
                    "attunement": "magenta"
                }
                magical_attribute_order = ["PWR","PRE","FRT","FLR","WIL","MLT","ATN"]
                attribute_index = 0
                attributes = game_state.text_adventure.player.attributes.__dict__.items()
                magical_attributes = game_state.text_adventure.player.magical_attributes.__dict__.items()
                for (attr_name, attr_value), (magical_attr_name, magical_attr_value) in zip(attributes, magical_attributes):
                    attr_color = attribute_colors.get(attr_name.lower(), "white")
                    attr_display_name = attribute_order[attribute_index]
                    magical_attr_color = magical_attribute_colors.get(magical_attr_name.lower(), "white")
                    magical_attr_display_name = magical_attribute_order[attribute_index]
                    stat_block += format_colored_text(f"{attr_display_name}: {attr_value}", color=attr_color) + "     | "
                    stat_block += format_colored_text(f"{magical_attr_display_name}: {magical_attr_value}", color=magical_attr_color) + "\n"
                    attribute_index += 1
                # print skills
                skills = game_state.text_adventure.player.skills.__dict__.items()
                stat_block += format_colored_text("Skills:", color="yellow") + "\n"
                for skill_name, skill_value in skills:
                    skill_display_name = skill_name.replace("_"," ").title()
                    stat_block += format_colored_text(f"{skill_display_name}:", color="grey") + " " + format_colored_text(f" {skill_value}", color="white") + "\n"
                print_in_box(stat_block.strip(), color="yellow")
            elif action_args[0].lower() == "take" or action_args[0].lower() == "get" or action_args[0].lower() == "pickup":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify an item to take.")
                    continue
                item_to_take = action_args[1]
                item_found = False
                for item in game_state.text_adventure.current_location.objects_in_location:
                    if item_to_take.lower() in item.name.lower():
                        game_state.text_adventure.player.inventory.append(item)
                        game_state.text_adventure.current_location.objects_in_location.remove(item)
                        item_found = True
                        print(f"You picked up the {item.name}.")
                        break
                    elif item.type_string.lower() == "container":
                        print(f"Searching {item.name} for {item_to_take}...")
                        for container_item in item.items:
                            if item_to_take.lower() in container_item.name.lower() or item_to_take.lower() in container_item.physical_description.lower():
                                game_state.text_adventure.player.inventory.append(container_item)
                                item.items.remove(container_item)
                                for location in game_state.text_adventure.locations:
                                    if location.name == game_state.text_adventure.current_location.name:
                                        location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                        break
                                item_found = True
                                print(f"You took the {container_item.name} from the {item.name}.")
                                game_state.text_adventure.roleplay(game_state.text_adventure.player, f"took the {container_item.name} from the {item.name}.", True)
                if not item_found:
                    for character in game_state.text_adventure.current_location.npcs_in_location:
                        print(f"Searching {character.full_name} for {item_to_take}...")
                        if character.worn_clothing.headwear != None:
                            if item_to_take.lower() in character.worn_clothing.headwear.name.lower() or item_to_take.lower() in character.worn_clothing.headwear.physical_description.lower():
                                if character.stats.hp <= 0:
                                    item_found = True
                                    game_state.text_adventure.player.inventory.append(character.worn_clothing.headwear)
                                    item_name = character.worn_clothing.headwear.name
                                    character.worn_clothing.headwear = None
                                    print(f"You took the {item_name} from {character.full_name}.")
                                    game_state.text_adventure.roleplay(game_state.text_adventure.player, f"took the {item_name} from {character.full_name}.", True)
                                else:
                                    item_found = True
                                    print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                                break
                        if character.worn_clothing.upperbodywear != None:
                            if item_to_take.lower() in character.worn_clothing.upperbodywear.name.lower() or item_to_take.lower() in character.worn_clothing.upperbodywear.physical_description.lower():
                                if character.stats.hp <= 0:
                                    item_found = True
                                    game_state.text_adventure.player.inventory.append(character.worn_clothing.upperbodywear)
                                    item_name = character.worn_clothing.upperbodywear.name
                                    character.worn_clothing.upperbodywear = None
                                    print(f"You took the {item_name} from {character.full_name}.")
                                    game_state.text_adventure.roleplay(game_state.text_adventure.player, f"took the {item_name} from {character.full_name}.", True)
                                else:
                                    item_found = True
                                    print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                                break
                        if character.worn_clothing.fullbodywear != None:
                            if item_to_take.lower() in character.worn_clothing.fullbodywear.name.lower() or item_to_take.lower() in character.worn_clothing.fullbodywear.physical_description.lower():
                                if character.stats.hp <= 0:
                                    item_found = True
                                    game_state.text_adventure.player.inventory.append(character.worn_clothing.fullbodywear)
                                    item_name = character.worn_clothing.fullbodywear.name
                                    character.worn_clothing.fullbodywear = None
                                    print(f"You took the {item_name} from {character.full_name}.")
                                    game_state.text_adventure.roleplay(game_state.text_adventure.player, f"took the {item_name} from {character.full_name}.", True)
                                else:
                                    item_found = True
                                    print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                                break
                        if character.worn_clothing.gloves != None:
                            if item_to_take.lower() in character.worn_clothing.gloves.name.lower() or item_to_take.lower() in character.worn_clothing.gloves.physical_description.lower():
                                if character.stats.hp <= 0:
                                    item_found = True
                                    game_state.text_adventure.player.inventory.append(character.worn_clothing.gloves)
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
                                    game_state.text_adventure.player.inventory.append(character.worn_clothing.lowerbodywear)
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
                                    game_state.text_adventure.player.inventory.append(character.worn_clothing.footwear)
                                    item_name = character.worn_clothing.footwear.name
                                    character.worn_clothing.footwear = None
                                    print(f"You took the {item_name} from {character.full_name}.")
                                else:
                                    item_found = True
                                    print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                                break
                        if character.equiped_item != None:
                            if item_to_take.lower() in character.equiped_item.name.lower() or item_to_take.lower() in character.equiped_item.physical_description.lower():
                                if character.stats.hp <= 0:
                                    item_found = True
                                    game_state.text_adventure.player.inventory.append(character.equiped_item)
                                    weapon_name = character.equiped_item
                                    character.equiped_item = None
                                    print(f"You took the {weapon_name} from {character.full_name}.")
                                else:
                                    item_found = True
                                    print(f"{character.full_name} is still alive. You can't take items from living characters. (yet)")
                                break
                        for item in character.inventory:
                            if item_to_take.lower() in item.name.lower() or item_to_take.lower() in item.physical_description.lower():
                                if character.stats.hp <= 0:
                                    # TODO: Ask the character if they want to give the item to the game_state.text_adventure.player
                                    game_state.text_adventure.player.inventory.append(item)
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
                                    game_state.text_adventure.player.inventory.append(item)
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
                    game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "drop" or action_args[0].lower() == "discard":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify an item to drop.")
                    continue
                item_to_drop = action_args[1]
                item_found = False
                for item in game_state.text_adventure.player.inventory:
                    if item_to_drop.lower() in item.name.lower() or item_to_drop.lower() in item.physical_description.lower():
                        game_state.text_adventure.current_location.objects_in_location.append(item)
                        game_state.text_adventure.player.inventory.remove(item)
                        for location in game_state.text_adventure.locations:
                            if location.name == game_state.text_adventure.current_location.name:
                                location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                break
                        item_found = True
                        print(f"You dropped the {item.name}.")
                        break
                if not item_found:
                    print(f"Item not found in your inventory: {item_to_drop}")
                else:
                    # pass_time = True
                    game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "put" or action_args[0].lower() == "placein" or action_args[0].lower() == "placeon":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify an item to put.")
                    continue
                item_to_put = action_args[1]
                item_found = None
                for item in game_state.text_adventure.player.inventory:
                    if item_to_put.lower() in item.name.lower():
                        inventory_found = item
                        break
                if inventory_found == None:
                    print(f"Item not found in your inventory: {item_to_put}")
                    continue
                where_to_put = input("Where would you like to put the item?> ")
                for item in game_state.text_adventure.current_location.objects_in_location:
                    if where_to_put.lower() in item.name.lower():
                        item.items.append(inventory_found)
                        game_state.text_adventure.player.inventory.remove(inventory_found)
                        for location in game_state.text_adventure.locations:
                            if location.name == game_state.text_adventure.current_location.name:
                                location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                break
                        item_found = True
                        print(f"You put the {inventory_found.name} in the {item.name}.")
                        break
                if not item_found:
                    print(f"Item not found in current location: {where_to_put}")
                else:
                    # pass_time = True
                    game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "equip" or action_args[0].lower() == "wear":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify an item to equip.")
                    continue
                item_to_equip = action_args[1]
                item_found = False
                for item in game_state.text_adventure.player.inventory:
                    if item_to_equip.lower() in item.name.lower() or item_to_equip.lower() in item.physical_description.lower():
                        if item.type_string.lower() == "weapon":
                            game_state.text_adventure.player.equiped_item = item
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You equipped the {item.name}.")
                            break
                        elif item.type_string.lower() == "headwear":
                            game_state.text_adventure.player.worn_clothing.headwear = item
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You equipped the {item.name}.")
                            break
                        elif item.type_string.lower() == "upperbodywear":
                            game_state.text_adventure.player.worn_clothing.upperbodywear = item
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You equipped the {item.name}.")
                            break
                        elif item.type_string.lower() == "lowerbodywear":
                            game_state.text_adventure.player.worn_clothing.lowerbodywear = item
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You equipped the {item.name}.")
                            break
                        elif item.type_string.lower() == "footwear":
                            game_state.text_adventure.player.worn_clothing.footwear = item
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You equipped the {item.name}.")
                            break
                        elif item.type_string.lower() == "gloves":
                            game_state.text_adventure.player.worn_clothing.gloves = item
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You equipped the {item.name}.")
                            break
                        elif item.type_string.lower() == "accessory":
                            game_state.text_adventure.player.worn_clothing.accessories.append(item)
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You equipped the {item.name}.")
                            break
                if not item_found:
                    print(f"Item not found in your inventory: {item_to_equip}")
                else:
                    # pass_time = True
                    game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "unequip" or action_args[0].lower() == "remove":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify an item to unequip.")
                    continue
                item_to_unequip = action_args[1]
                item_found = False
                if game_state.text_adventure.player.equiped_item != None:
                    if item_to_unequip.lower() in game_state.text_adventure.player.equiped_item.name.lower() or item_to_unequip.lower() in game_state.text_adventure.player.equiped_item.physical_description.lower():
                        game_state.text_adventure.player.inventory.append(game_state.text_adventure.player.equiped_item)
                        game_state.text_adventure.player.equiped_item = None
                        item_found = True
                        print(f"You unequipped the {item_to_unequip}.")
                if game_state.text_adventure.player.worn_clothing.headwear != None:
                    if item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.headwear.name.lower() or item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.headwear.physical_description.lower():
                        game_state.text_adventure.player.inventory.append(game_state.text_adventure.player.worn_clothing.headwear)
                        game_state.text_adventure.player.worn_clothing.headwear = None
                        item_found = True
                        print(f"You unequipped the {item_to_unequip}.")
                if game_state.text_adventure.player.worn_clothing.upperbodywear != None:
                    if item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.upperbodywear.name.lower() or item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.upperbodywear.physical_description.lower():
                        game_state.text_adventure.player.inventory.append(game_state.text_adventure.player.worn_clothing.upperbodywear)
                        game_state.text_adventure.player.worn_clothing.upperbodywear = None
                        item_found = True
                        print(f"You unequipped the {item_to_unequip}.")
                if game_state.text_adventure.player.worn_clothing.fullbodywear != None:
                    if item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.fullbodywear.name.lower() or item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.fullbodywear.physical_description.lower():
                        game_state.text_adventure.player.inventory.append(game_state.text_adventure.player.worn_clothing.fullbodywear)
                        game_state.text_adventure.player.worn_clothing.fullbodywear = None
                        item_found = True
                        print(f"You unequipped the {item_to_unequip}.")
                if game_state.text_adventure.player.worn_clothing.gloves != None:
                    if item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.gloves.name.lower() or item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.gloves.physical_description.lower():
                        game_state.text_adventure.player.inventory.append(game_state.text_adventure.player.worn_clothing.gloves)
                        game_state.text_adventure.player.worn_clothing.gloves = None
                        item_found = True
                        print(f"You unequipped the {item_to_unequip}.")
                if game_state.text_adventure.player.worn_clothing.lowerbodywear != None:
                    if item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.lowerbodywear.name.lower() or item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.lowerbodywear.physical_description.lower():
                        game_state.text_adventure.player.inventory.append(game_state.text_adventure.player.worn_clothing.lowerbodywear)
                        game_state.text_adventure.player.worn_clothing.lowerbodywear = None
                        item_found = True
                        print(f"You unequipped the {item_to_unequip}.")
                if game_state.text_adventure.player.worn_clothing.footwear != None:
                    if item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.footwear.name.lower() or item_to_unequip.lower() in game_state.text_adventure.player.worn_clothing.footwear.physical_description.lower():
                        game_state.text_adventure.player.inventory.append(game_state.text_adventure.player.worn_clothing.footwear)
                        game_state.text_adventure.player.worn_clothing.footwear = None
                        item_found = True
                        print(f"You unequipped the {item_to_unequip}.")
                if len(game_state.text_adventure.player.worn_clothing.accessories) > 0:
                    for item in game_state.text_adventure.player.worn_clothing.accessories:
                        if item_to_unequip.lower() in item.name.lower() or item_to_unequip.lower() in item.physical_description.lower():
                            game_state.text_adventure.player.inventory.append(item)
                            game_state.text_adventure.player.worn_clothing.accessories.remove(item)
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
                # for item in game_state.text_adventure.items:
                #     if item_to_spawn.lower() in item.name.lower() or item_to_spawn.lower() in item.physical_description.lower():
                #         game_state.text_adventure.current_location.objects_in_location.append(item)
                #         item_found = True
                #         print(f"You spawned '{item.name}' in the current location.")
                #         break
                # if not item_found:
                # Generate the item
                item = game_state.text_adventure.generate_item_from_prompt(item_to_spawn)
                game_state.text_adventure.current_location.objects_in_location.append(item)
                item_found = True
                print(f"You spawned '{item.name}' in the current location.")
            elif action_args[0].lower() == "spawn_character":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify a character to spawn.")
                    continue
                character_to_spawn = action_args[1]
                # character_found = False
                # for character in game_state.text_adventure.characters:
                #     if character_to_spawn.lower() in character.full_name.lower():
                #         game_state.text_adventure.current_location.npcs_in_location.append(character)
                #         character_found = True
                #         print(f"You spawned '{character.full_name}' in the current location.")
                #         break
                # if not character_found:
                # Generate the character
                character = game_state.text_adventure.generate_character_from_prompt(character_to_spawn)
                game_state.text_adventure.current_location.npcs_in_location.append(character)
                character_found = True
                print(f"You spawned '{character.full_name}' in the current location.")
            elif action_args[0].lower() == "say":
                message = action.split(" ", 1)
                if len(message) < 2:
                    print("Please specify a message to say.")
                    continue
                # print(f"You say: {message[1]} (This feature is not yet implemented.)")
                game_state.text_adventure.say(game_state.text_adventure.player, message[1], True)
                # pass_time = True
                game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "find" or action_args[0].lower() == "search" or action_args[0].lower() == "lookfor" or action_args[0].lower() == "searchfor" or action_args[0].lower() == "lookaround" or action_args[0].lower() == "look" and action_args[1] == "around" or action_args[0].lower() == "searcharound" or action_args[0].lower() == "search" and action_args[1] == "around":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print_colored(f"You start looking around...","grey")
                    found = game_state.text_adventure.find_item()
                else:
                    to_find_prompt = action_args[1]
                    print(f"{bcolors.GREY}You start looking for{bcolors.ENDC} '{bcolors.CYAN}{to_find_prompt}{bcolors.ENDC}'{bcolors.GREY}...{bcolors.ENDC}")
                    found = game_state.text_adventure.find_item(to_find_prompt)
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
                        for itm in game_state.text_adventure.current_location.objects_in_location:
                            if item.name.lower() in itm.name.lower():
                                already_exists = True
                                if verbose:
                                    print_colored(f"'{item.name}' already exists in the current location.", "red")
                                break
                        if not already_exists:
                            game_state.text_adventure.current_location.objects_in_location.append(item)
                            found_item = True
                            print(f"You found '{bcolors.BLUE}{item.name}{bcolors.ENDC}' in the current location.")
                    for character in found["characters"]:
                        # if not already exists
                        already_exists = False
                        for char in game_state.text_adventure.current_location.npcs_in_location:
                            if character.full_name.lower() in char.full_name.lower():
                                already_exists = True
                                if verbose:
                                    print_colored(f"'{character.full_name}' already exists in the current location.", "red")
                                break
                        if not already_exists:
                            game_state.text_adventure.current_location.npcs_in_location.append(character)
                            found_item = True
                            print(f"You found '{bcolors.BLUE}{character.get_unknown_description()}{bcolors.ENDC}' in the current location.")
                    for travelable_location in found["travelable_locations"]:
                        # if not already exists
                        already_exists = False
                        for travelable_loc in game_state.text_adventure.current_location.travel_destinations:
                            if travelable_location.location_name.lower() in travelable_loc.location_name.lower():
                                already_exists = True
                                if verbose:
                                    print_colored(f"'{travelable_location.location_name}' already exists in the current location.", "red")
                                break
                        if not already_exists:
                            game_state.text_adventure.current_location.travel_destinations.append(travelable_location)
                            found_item = True
                            print(f"You found '{bcolors.BLUE}{travelable_location.location_name}{bcolors.ENDC}' in the current location.")
                if verbose:
                    # print(f"You found {len(found['items'])} items, {len(found['characters'])} characters and {len(found['travelable_locations'])} travelable locations.")
                    print_colored(f"You found {len(found['items'])} items, {len(found['characters'])} characters and {len(found['travelable_locations'])} travelable locations.", "yellow")
                if found_item:
                    should_refresh = True
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
                game_state.text_adventure.roleplay(game_state.text_adventure.player, message[1], True)
                # pass_time = True
                game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "read":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify an item to read.")
                    continue
                item_to_read = action_args[1]
                item_found = False
                for item in game_state.text_adventure.player.inventory:
                    if item_to_read.lower() in item.name.lower() or item_to_read.lower() in item.physical_description.lower():
                        if item.type_string.lower() == "book":
                            print(f"You start reading '{bcolors.BLUE}{item.name}{bcolors.ENDC}'.")
                            game_state.text_adventure.roleplay(game_state.text_adventure.player, f"is reading '{item.name}'", True)

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
                    game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "eat" or action_args[0].lower() == "consume":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify an item to eat.")
                    continue
                item_to_eat = action_args[1]
                item_found = False
                for item in game_state.text_adventure.player.inventory:
                    if item_to_eat.lower() in item.name.lower() or item_to_eat.lower() in item.physical_description.lower():
                        if item.type_string.lower() == "food":
                            game_state.text_adventure.player.stats.hunger += item.hunger_restored
                            game_state.text_adventure.player.stats.thirst += item.thirst_restored
                            game_state.text_adventure.player.stats.hp += item.health_restored
                            game_state.text_adventure.player.inventory.remove(item)
                            for location in game_state.text_adventure.locations:
                                if location.name == game_state.text_adventure.current_location.name:
                                    location.objects_in_location = game_state.text_adventure.current_location.objects_in_location
                                    break
                            item_found = True
                            print(f"You ate the {item.name}.")
                            break
                if not item_found:
                    print(f"Item not found in your inventory: {item_to_eat}")
                else:
                    # pass_time = True
                    game_state.text_adventure.player.stats.action_points -= 1
            elif action_args[0].lower() == "attack" or action_args[0].lower() == "fight" or action_args[0].lower() == "kill" or action_args[0].lower() == "hit" or action_args[0].lower() == "hurt" or action_args[0].lower() == "shoot" or action_args[0].lower() == "punch" or action_args[0].lower() == "stab" or action_args[0].lower() == "slash":
                action_args = action.split(" ", 1)
                if len(action_args) < 2:
                    print("Please specify a character to attack.")
                    continue
                character_to_attack = action_args[1]
                character_found = False
                if game_state.text_adventure.player.equiped_item == None:
                    print("You need a weapon equipped to attack.")
                    continue
                for character in game_state.text_adventure.current_location.npcs_in_location:
                    if character_to_attack.lower() in character.full_name.lower() or character_to_attack.lower() in character.get_unknown_description().lower():
                        character_found = True
                        # character.stats.hp -= game_state.text_adventure.player.equiped_item.damage
                        # Roll for damage
                        max_dies = game_state.text_adventure.player.equiped_item.dies_to_roll
                        sides = game_state.text_adventure.player.equiped_item.max_damage_per_die
                        dies = [random.randint(1, sides) for _ in range(max_dies)]
                        print(f"You roll the dice for damage: {dies} (Total: {sum(dies)})")
                        character.stats.hp -= sum(dies) + game_state.text_adventure.player.equiped_item.damage_modifier
                        damage = sum(dies) + game_state.text_adventure.player.equiped_item.damage_modifier
                        if character.stats.hp <= 0:
                            if game_state.text_adventure.player.equiped_item:
                                print(f"You attacked {character.full_name} with your {game_state.text_adventure.player.equiped_item.name} and killed them.")
                            else:
                                print(f"You beat {character.full_name} to death with your bare hands.")
                        else:
                            if game_state.text_adventure.player.equiped_item:
                                print(f"You attacked {character.full_name} with your {game_state.text_adventure.player.equiped_item.name}.")
                            else:
                                print(f"You attacked {character.full_name} with your fists.")
                # pass_time = True
                game_state.text_adventure.player.stats.action_points -= 1
            elif action.lower() == "quit" or action.lower() == "exit" or action.lower() == "q":
                print("Quitting the game...")
                self.in_world = False
                self.in_game = False
                break
            elif action_args[0].lower() == "save":
                if len(action_args) < 2:
                    save_name = input("Enter a name for the save file: ")
                    if save_name.strip() == "":
                        save_name = None
                else:
                    save_name = action.split(" ", 1)[1].replace(" ", "_")
                self.trigger_save(save_name)
            elif action.lower() == "load":
                save_name = input("Enter the name of the save file to load: ")
                print("Loading the game...")
                game_state.load(save_name)
                print("Game loaded.")
            elif action.lower() == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                self.print_current_screen()
            elif action.lower() == "pass":
                # pass_time = True
                wait()
            elif action.lower() == "reset_story": # Assign new random story.id
                game_state.text_adventure.reset_story()
            elif action.lower() == "reset_id":
                game_state.text_adventure.reset_id()
            elif action.lower() == "leave_world":
                self.in_world = False
                print("You close your eyes, and the world fades away. When you open them again, you find yourself back at the rock floating in the void.")
            else:
                # print("Invalid command. Type 'help' for a list of commands.")
                if action.strip() != "":
                    game_state.text_adventure.say(game_state.text_adventure.player, action, True)
                else:
                    wait()
            if game_state.text_adventure.player.stats.action_points == 0:
                # AI Reaction/AI Turn
                if prototype_ai_turns:
                    ai_turn = game_state.text_adventure.ai_turn()
                if prototype_ai_game_master:
                    should_refresh = game_state.text_adventure.game_master_turn()
            if should_refresh:
                self.print_current_screen()



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the prototype AI.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--no-prototype-ai-turns", action="store_false", help="Disable prototype AI turns.")
    parser.add_argument("--no-prototype-ai-game-master", action="store_false", help="Disable prototype AI game master.")
    parser.add_argument("--clear-console", action="store_true", help="Enable clearing the console.")
    parser.add_argument("--skip-cutscene", action="store_true", help="Enable skipping cutscenes.")
    parser.add_argument("--auto-start", action="store_true", help="Automatically start a new game without going through the main menu.")
    parser.add_argument("--save-name", type=str, default=None, help="Name of the save file to load automatically.")
    parser.add_argument("--player-prompt", type=str, default=None, help="Custom player prompt to start the game with.")
    parser.add_argument("--room-prompt", type=str, default=None, help="Custom room description prompt to start the game with.")
    parser.add_argument("--first-story-prompt", type=str, default=None, help="Custom story aesthetic to start the game with.")
    args = parser.parse_args()
    os.makedirs("saves", exist_ok=True)
    verbose = args.verbose
    prototype_ai_turns = args.no_prototype_ai_turns
    prototype_ai_game_master = args.no_prototype_ai_game_master
    should_clear_console = args.clear_console
    skip_cutscene = args.skip_cutscene
    auto_start = args.auto_start
    save_name = args.save_name
    player_prompt = args.player_prompt
    room_prompt = args.room_prompt
    first_story_prompt = args.first_story_prompt

    print_colored("Temp: "+str(temp), "green")
    print_colored("Top P: "+str(top_p), "green")
    print_colored("Min P: "+str(min_p), "green")
    print_colored("Max Tokens: "+str(max_tokens), "green")
    print_colored("Model Name: "+model_name, "green")
    print_colored("API URL: "+api_url, "green")

    if verbose:
        print_colored("-----------------------", "yellow")
        print_colored("Verbose output enabled.", "yellow")
        print_colored("Prototype AI turns: " + str(prototype_ai_turns), "yellow")
        print_colored("Prototype AI game master: " + str(prototype_ai_game_master), "yellow")

    



    tprint("Welcome to...")
    while True: # Main Menu Loop - L1
        if should_clear_console:
            clear_console()
        game_state: GameState = None
        tprint("AI Text Adventure",font="georgi16")
        print_colored("What would you like to do?", color="cyan")
        print(f'{format_colored_text("start", color="red")} {format_colored_text("- Start a new game", color="grey")}')
        print(f'{format_colored_text("load", color="red")} {format_colored_text("- Load a saved game", color="grey")}')
        print(f'{format_colored_text("quit", color="red")} {format_colored_text("- Quit the game", color="grey")}')
        if auto_start:
            menu_choice = "start"
            auto_start = False
        else:
            menu_choice = input(">").lower()

        if menu_choice == "start" or menu_choice == "s" or menu_choice == "new":
            if save_name is None:
                save_name = input("Enter a name for your save file, if the file exists it will be overwritten: ")
                if os.path.exists(f"saves/{save_name}/game_state.json"):
                    overwrite = input(f"A save file with the name '{save_name}' already exists. Overwrite? (y/n): ")
                    if overwrite.lower() != "y":
                        print_colored("Save file not overwritten. Returning to main menu.", color="red")
                        continue
            print_colored("Starting a new game...", color="cyan")
            game_state = GameState(save_name=save_name, api_key=api_key, api_url=api_url, model_name=model_name, openrouter_style_api=openrouter_style_api, temp=temp, top_p=top_p, min_p=min_p, max_tokens=max_tokens, verbose=verbose)
            # test_story = game_state.text_adventure.generate_story("Ponyville")
            game_state.opening_cutscene(skip_cutscene, player_prompt, room_prompt, first_story_prompt)
            game_state.save()
        elif menu_choice == "load":
            save_name = input("Enter the name of the game to load, or nothing to load current save: ")
            game_state = GameState(save_name=save_name, api_key=api_key, api_url=api_url, model_name=model_name, openrouter_style_api=openrouter_style_api, temp=temp, top_p=top_p, min_p=min_p, max_tokens=max_tokens, verbose=verbose)
            print_colored("Loading the game...", color="cyan")
            game_state.load(save_name)
            # game_state.text_adventure.load_game(save_name)
            # print(f"Welcome back {game_state.text_adventure.player.full_name}!")
            print_colored(f"Welcome back {game_state.player.full_name}!", color="green")
        elif menu_choice == "quit":
            print_colored("Quitting the game. Goodbye!", color="cyan")
            break
        else:
            print_colored("Invalid choice. Please try again.", "red")
            continue
        
        game_state.hub_loop()

print_colored("Exited the game. Goodbye!", color="cyan")