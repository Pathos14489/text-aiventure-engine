from pydantic import BaseModel, Field
from typing import Union

from .spell_effects import SpellEffect

class Spell(BaseModel):
    """Spell Schema - A spell in a text adventure game. All fields are required to have a value. Spells can be used by characters to cast magic. Spells can have different effects, such as damage, healing, buffs, debuffs, etc."""
    name: str = Field(...,description="The name of the spell. Should be at least a sentence long.", min_length=1, pattern="^([a-zA-Z0-9- '])+$", examples=[
        "Fireball",
        "Teleport Self to the Moon",
        "Healing Light",
        "Strength of the Bear",
        "Avada Kedavra"
    ])
    skill_level_required: str = Field(...,description="The level of skill required to use the weapon. Novice:0, Apprentice: 20, Journeyman: 40, Expert: 60, Master: 80", examples=[
        "novice",
        "apprentice",
        "journeyman",
        "expert",
        "master"
    ], pattern="^(novice|apprentice|journeyman|expert|master)$")
    description: str = Field(...,description="A description of the spell. Should be at least a sentence long.", min_length=1)
    mana_cost: int = Field(...,ge=0,description="The amount of mana required to cast the spell.")
    effects_prompt: str = Field(...,description="The effect of the spell. Should be a short description of the spell's effect.", min_length=1)
    effects: list[SpellEffect] = Field(...,description="A list of effects that the spell has when cast.", min_length=1)
