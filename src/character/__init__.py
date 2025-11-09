from pydantic import BaseModel, Field
from typing import Union

from src.regex_patterns import hex_pattern
from src.utils import generate_id, preprocess, bcolors
from .stats import Attributes, MagicalAttributes, Stats, Skills
from .worn_clothing import WornClothing
import src.items as Items
from .body_part_descriptions import BodyPartDescriptions
from .character_card import CharacterCard

class Character(BaseModel):
    """Character Schema - No stats, just descriptions. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that Personality, Appearance, and Scenario are all separate sections. that should cohesively flow together, seperated by new lines, and not repeat themselves. Drives are what motivates the character, and can be things like "Revenge on the bandits who killed their family" or "To find the lost city of gold". Tags are used to help search for characters, and can be things like "Elf", "Wizard", "Pirate", etc. The voice description is seperate from the other descriptions, and should be able to exist by itself without the other descriptions. It should describe how the character should sound. All descriptions should be at least a paragraph long, and the first message should be at least a sentence long, but longer is not bad. The backstory is the character's history, and should be at least a paragraph long. The naked body description is what the character looks like without clothes, and should be at least a paragraph long and explicitly and graphically describe the character's nude body. All fields are required to have a value. Make sure characters are wearing adequate clothing for the scenario requested(or lack of clothing if it's necessary). Example: If someone is from the middle ages, they should be wearing era appropriate equipemnt!"""
    id: str = Field(default_factory=generate_id)
    full_name: str = Field(..., min_length=1) # Tricks the LLM into prompting itself to generate a name
    nick_name: str = Field(..., min_length=1)
    age: int = Field(...)
    gender: str = Field(...,examples=["Male","Female"],pattern="^(Male|Female)$")
    race: str
    racial_gender_term: str = Field(...,examples=["Man", "Boy", "Woman", "Girl"], description="The gender term specific to this character. For example, an adult human male would be 'man', a child male would be a 'boy', etc.")
    species: str
    attributes: Attributes
    magical_attributes: MagicalAttributes
    stats: Stats = Field(description="The character's stats. This is used for things like how much damage the character can take before dying, etc.")
    skills: Skills = Field(...,description="The character's skills. This is used for things like how good the character is at certain tasks, etc.")
    clothing_prompt: str = Field(...,description="A description of the character's clothing. Should be at least a sentence long.", min_length=1) # Tricks the LLM into prompting itself to generate clothing
    worn_clothing: WornClothing = Field(...,description="The character's clothing that they're wearing or not wearing. This is used for things like what the character is wearing, what weapons they have, etc.")
    equiped_item: Union[Items.Weapon,None] = Field(description="The weapon that the character has equiped. If the character has no weapon equiped, this property should be null.")
    inventory: list[Items.SomeItem] = Field(description="A list of objects that the character has on them. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required Attributes. If an item is a weapon, it MUST have a damage value and required Attributes. If an item is food, it MUST have a hunger restored and thirst restored value. This is not worn equipment, but items that the character has in their inventory. To be in a characters inventory, they must be actively carrying the item. Items in the inventory are not equiped, and are not being worn by the character. They CANNOT be on the ground, in a box, on a table, etc. They MUST be in the character's possession on their person.")
    hex_color: str = Field(...,description="The hex color code for the character's name. Should be a 6 character hex code, without the #.",pattern=hex_pattern)
    personality_description: str
    naked_body_part_descriptions: BodyPartDescriptions
    backstory: str = Field(...,description="A description of the character's backstory. Should be at least a paragraph long.", min_length=1)
    processing: bool = True

    def __init__(self, **data):
        # Preprocess the data to make sure all int fields are within le and ge constraints
        data = preprocess(data)
        if not isinstance(data['attributes'], Attributes):
            data['attributes'] = Attributes.from_json(data['attributes'])
        if not isinstance(data['magical_attributes'], MagicalAttributes):
            data['magical_attributes'] = MagicalAttributes.from_json(data['magical_attributes'])
        if not isinstance(data['stats'], Stats):
            data['stats'] = Stats.from_json(data['stats'])
        if not isinstance(data['skills'], Skills):
            data['skills'] = Skills.from_json(data['skills'])
        if 'worn_clothing' in data and data['worn_clothing'] is not None and not isinstance(data['worn_clothing'], WornClothing):
            data['worn_clothing'] = WornClothing.from_json(data['worn_clothing'])
        if 'inventory' in data and data['inventory'] is not None:
            inventory_items = []
            for item in data['inventory']:
                if not isinstance(item, Items.SomeItem):
                    inventory_items.append(Items.from_json(item))
                else:
                    inventory_items.append(item)
            data['inventory'] = inventory_items
        if 'naked_body_part_descriptions' in data and not isinstance(data['naked_body_part_descriptions'], BodyPartDescriptions):
            data['naked_body_part_descriptions'] = BodyPartDescriptions.from_json(data['naked_body_part_descriptions'])
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
                description += f"{self.naked_body_part_descriptions.naked_upper_body_description}.\n"
            if not self.worn_clothing.upperbodywear.covers_belly and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_belly):
                description += f"{self.naked_body_part_descriptions.abdomen_description}.\n"
        else:
            if self.worn_clothing.fullbodywear:
                description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.fullbodywear.physical_description[0].lower()}{self.worn_clothing.fullbodywear.physical_description[1:]}.\n"
                if not self.worn_clothing.fullbodywear.covers_breasts:
                    description += f"{self.naked_body_part_descriptions.naked_upper_body_description}.\n"
                if not self.worn_clothing.fullbodywear.covers_belly:
                    description += f"{self.naked_body_part_descriptions.abdomen_description}.\n"
            else:
                if self.worn_clothing.upperbody_underwear:
                    description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.upperbody_underwear.physical_description[0].lower()}{self.worn_clothing.upperbody_underwear.physical_description[1:]}.\n"
                else:
                    description += f"{self.naked_body_part_descriptions.naked_upper_body_description}.\n"
                description += f"{self.naked_body_part_descriptions.abdomen_description}.\n"
        if self.worn_clothing.gloves:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.gloves.physical_description[0].lower()}{self.worn_clothing.gloves.physical_description[1:]}.\n"
        else:
            description += f"{self.naked_body_part_descriptions.hands_description}.\n"
        if self.worn_clothing.lowerbodywear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.lowerbodywear.physical_description[0].lower()}{self.worn_clothing.lowerbodywear.physical_description[1:]}.\n"
            if not self.worn_clothing.lowerbodywear.covers_legs and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_legs):
                description += f"{self.naked_body_part_descriptions.legs_description}.\n"
            if not self.worn_clothing.lowerbodywear.covers_genitals and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_genitals) and not self.worn_clothing.lower_underwear:
                description += f"{self.naked_body_part_descriptions.naked_genital_description}.\n"
            if not self.worn_clothing.lowerbodywear.covers_butt and (not self.worn_clothing.fullbodywear or not self.worn_clothing.fullbodywear.covers_butt):
                description += f"{self.naked_body_part_descriptions.butt_description}.\n"
        else:
            if self.worn_clothing.fullbodywear:
                if not self.worn_clothing.fullbodywear.covers_legs:
                    description += f"{self.naked_body_part_descriptions.legs_description}.\n"
                if not self.worn_clothing.fullbodywear.covers_genitals:
                    if not self.worn_clothing.lower_underwear:
                        description += f"{self.naked_body_part_descriptions.naked_genital_description}.\n"
                    else:
                        description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.lower_underwear.physical_description[0].lower()}{self.worn_clothing.lower_underwear.physical_description[1:]}.\n"
                else:
                    description += f"{self.naked_body_part_descriptions.legs_description}.\n"
                if not self.worn_clothing.fullbodywear.covers_butt and not self.worn_clothing.lower_underwear:
                    description += f"{self.naked_body_part_descriptions.butt_description}.\n"
                else:
                    description += f"{self.naked_body_part_descriptions.butt_description}.\n"
            else:
                if not self.worn_clothing.lower_underwear:
                    description += f"{self.naked_body_part_descriptions.naked_genital_description}.\n"
                else:
                    description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.lower_underwear.physical_description[0].lower()}{self.worn_clothing.lower_underwear.physical_description[1:]}.\n"
        if self.worn_clothing.footwear:
            description += f"{self.get_pronouns()['subject'].capitalize()}'s wearing {self.worn_clothing.footwear.physical_description[0].lower()}{self.worn_clothing.footwear.physical_description[1:]}.\n"
        else:
            description += f"{self.naked_body_part_descriptions.feet_description}\n"
        if self.stats.hp <= 0:
            description += f"{self.get_pronouns()['subject'].capitalize()} is dead."
            if self.equiped_item:
                description += f"{self.get_pronouns()['object'].capitalize()} weapon, a {self.equiped_item.physical_description}, is lying on the ground beside {self.get_pronouns()['object']} body."
        else:
            if self.equiped_item:
                description += f"{self.get_pronouns()['subject'].capitalize()} is holding {self.equiped_item.physical_description}."
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
        if self.equiped_item:
            description += f"{self.get_pronouns()['subject'].capitalize()} is holding {self.equiped_item.physical_description[0].lower()}{self.equiped_item.physical_description[1:]}. "
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

    def to_json(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "nick_name": self.nick_name,
            "age": self.age,
            "gender": self.gender,
            "race": self.race,
            "racial_gender_term": self.racial_gender_term,
            "species": self.species,
            "attributes": self.attributes.to_json(),
            "magical_attributes": self.magical_attributes.to_json(),
            "stats": self.stats.to_json(),
            "skills": self.skills.to_json(),
            "clothing_prompt": self.clothing_prompt,
            "worn_clothing": self.worn_clothing.to_json() if self.worn_clothing else None,
            "equiped_item": self.equiped_item.to_json() if self.equiped_item else None,
            "inventory": [item.to_json() for item in self.inventory],
            "hex_color": self.hex_color,
            "personality_description": self.personality_description,
            "naked_body_part_descriptions": self.naked_body_part_descriptions.to_json(),
            "backstory": self.backstory,
            "processing": self.processing
        }
    
    @staticmethod
    def from_json(data: dict) -> "Character":
        """Deserialize a JSON object into a Character instance."""
        data['attributes'] = Attributes.from_json(data['attributes'])
        data['magical_attributes'] = MagicalAttributes.from_json(data['magical_attributes'])
        data['stats'] = Stats.from_json(data['stats']) if 'stats' in data and data['stats'] is not None else Stats(hp=100,hunger=100,thirst=100)
        data['skills'] = Skills.from_json(data['skills'])
        data['inventory'] = [Items.from_json(item) for item in data.get('inventory', [])]
        if 'worn_clothing' in data and data['worn_clothing'] is not None:
            data['worn_clothing'] = WornClothing.from_json(data['worn_clothing'])
        if 'equiped_item' in data and data['equiped_item'] is not None:
            data['equiped_item'] = Items.from_json(data['equiped_item'])
        data['naked_body_part_descriptions'] = BodyPartDescriptions.from_json(data['naked_body_part_descriptions'])
        if "clothing_prompt" not in data:
            data["clothing_prompt"] = "N/A"
        return Character(**data)

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
