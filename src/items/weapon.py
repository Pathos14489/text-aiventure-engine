from pydantic import  Field

from src.items.base_item import BaseItem
from src.regex_patterns import lower_single_sentence
from src.utils import generate_id

class Weapon(BaseItem):
    """Weapon Schema - A weapon item in a text adventure game. Unless a weapon is super complicated, most requirements should be below 5. Anything over 5 for a required Attribute is considered very high, and should be reserved for very powerful weapons. Only Weapon Items should have a damage value and required Attributes."""
    type_string: str = Field(description="The type of item.", pattern="^Weapon$")
    skill_type: str = Field(...,description="The type of skill required to use the weapon.", examples=[
        "melee",
        "unarmed",
        "firearms",
        "energy weapons",
        "explosives"
    ], pattern="^(melee|unarmed|firearms|energy weapons|explosives)$")
    skill_level_required: str = Field(...,description="The level of skill required to use the weapon. Novice:0, Apprentice: 20, Journeyman: 40, Expert: 60, Master: 80", examples=[
        "novice",
        "apprentice",
        "journeyman",
        "expert",
        "master"
    ], pattern="^(novice|apprentice|journeyman|expert|master)$")
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
    max_damage_per_die: int = Field(...,description="The amount of damage the weapon does. Should be a number between 0 and 100, but can go higher if you want to be extra.")
    damage_modifier: int = Field(...,description="The flat damage modifier added to the weapon's damage roll.")
    dies_to_roll: int = Field(...,description="The number of dice to roll for damage. Should be a number between 1 and 10.")
    strength_required: int = Field(...,description="The amount of strength required to wield the weapon. Should be a number between 1 and 10.", le=10)
    intelligence_required: int = Field(...,description="The amount of intelligence required to wield the weapon. Should be a number between 1 and 10.", le=10)
    agility_required: int = Field(...,description="The amount of agility required to wield the weapon. Should be a number between 1 and 10.", le=10)

    def to_json(self):
        json_out = super().to_json()
        json_out.update({
            "skill_type": self.skill_type,
            "skill_level_required": self.skill_level_required,
            "max_damage_per_die": self.max_damage_per_die,
            "damage_modifier": self.damage_modifier,
            "dies_to_roll": self.dies_to_roll,
            "strength_required": self.strength_required,
            "intelligence_required": self.intelligence_required,
            "agility_required": self.agility_required
        })
        return json_out
    
    @staticmethod
    def from_json(data: dict) -> "Weapon":
        """Deserialize a JSON object into a Weapon instance."""
        if "id" not in data:
            data["id"] = generate_id()
        return Weapon(**data)