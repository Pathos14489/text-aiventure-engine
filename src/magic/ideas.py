from pydantic import BaseModel, Field
from typing import Union

from src.items import Weapon, Food, Headwear, Footwear, Gloves, LowerBodywear, UpperBodywear, Accessory
from src.magic.spell_effects import SpellEffect

class MagicWeapon(Weapon):
    """Magic Weapon Schema - A magic weapon item in a text adventure game. All fields are required to have a value. Magic weapons are weapons that have magical properties or effects. Magic weapons can have different effects, such as damage, healing, buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicWeapon$")
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
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the weapon as a list of spell effects that the weapon has when used.", min_length=1)

class MagicFood(Food):
    """Magic Food Schema - A magic food item in a text adventure game. All fields are required to have a value. Magic food is food that has magical properties or effects. Magic food can have different effects, such as healing, buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicFood$")
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the food as a list of spell effects that the food has when consumed.", min_length=1)

# Clothing Schemas
# Magical Clothing Schemas
class MagicHeadwear(Headwear):
    """Magic Headwear Schema - A magic headwear item in a text adventure game. All fields are required to have a value. Magic headwear are headwear that have magical properties or effects. Magic headwear can have different effects, such as buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicHeadwear$")
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the headwear as a list of spell effects that the headwear has when worn.", min_length=1)

class MagicFootwear(Footwear):
    """Magic Footwear Schema - A magic footwear item in a text adventure game. All fields are required to have a value. Magic footwear are footwear that have magical properties or effects. Magic footwear can have different effects, such as buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicFootwear$")
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the footwear as a list of spell effects that the footwear has when worn.", min_length=1)

class MagicGloves(Gloves):
    """Magic Gloves Schema - A magic gloves item in a text adventure game. All fields are required to have a value. Magic gloves are gloves that have magical properties or effects. Magic gloves can have different effects, such as buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicGloves$")
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the gloves as a list of spell effects that the gloves have when worn.", min_length=1)

class MagicLowerBodywear(LowerBodywear):
    """Magic LowerBodywear Schema - A magic lowerbodywear item in a text adventure game. All fields are required to have a value. Magic lowerbodywear are lowerbodywear that have magical properties or effects. Magic lowerbodywear can have different effects, such as buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicLowerBodywear$")
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the lowerbodywear as a list of spell effects that the lowerbodywear has when worn.", min_length=1)

class MagicUpperBodywear(UpperBodywear):
    """Magic UpperBodywear Schema - A magic upperbodywear item in a text adventure game. All fields are required to have a value. Magic upperbodywear are upperbodywear that have magical properties or effects. Magic upperbodywear can have different effects, such as buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicUpperBodywear$")
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the upperbodywear as a list of spell effects that the upperbodywear has when worn.", min_length=1)

class MagicAccessory(Accessory):
    """Magic Accessory Schema - A magic accessory item in a text adventure game. All fields are required to have a value. Magic accessories are accessories that have magical properties or effects. Magic accessories can have different effects, such as buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^MagicAccessory$")
    magical_effects: list[SpellEffect] = Field(...,description="The magical effects of the accessory as a list of spell effects that the accessory has when worn.", min_length=1)
