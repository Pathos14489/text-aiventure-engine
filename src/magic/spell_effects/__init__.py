from pydantic import BaseModel, Field
from typing import Union

from .damage_other import DamageOtherSpellEffect
from .damage_self import DamageSelfSpellEffect
from .heal_other import HealOtherSpellEffect
from .heal_self import HealSelfSpellEffect
from .buff_other import BuffOtherSpellEffect
from .buff_self import BuffSelfSpellEffect
from .debuff_other import DebuffOtherSpellEffect
from .debuff_self import DebuffSelfSpellEffect
from .teleport_self import TeleportSelfSpellEffect
from .teleport_other import TeleportOtherSpellEffect

class SpellEffect(BaseModel):
    """Spell Effect Schema - An effect of a spell in a text adventure game. All fields are required to have a value. Spell effects can be used to define the effects of a spell when it is cast. Spell effects can have different types, such as damage, healing, buffs, debuffs, etc."""
    type_string: str = Field(...,description="The type of spell effect.", pattern="^SpellEffect$")
    effect_prompt: str = Field(...,description="A prompt describing the spell effect. Should be a short description of the spell effect.", min_length=1)
    effect_name: str = Field(...,description="The name of the spell effect in universe.", min_length=1, pattern="^([a-zA-Z0-9- '])+$", examples=[
        "Fire Essence",
        "Ignis",
        "Azapheria",
        "Healing Component",
        "Aegis Rune"
    ])
    effect: Union[
        DamageOtherSpellEffect,
        DamageSelfSpellEffect,
        HealOtherSpellEffect,
        HealSelfSpellEffect,
        BuffOtherSpellEffect,
        BuffSelfSpellEffect,
        DebuffOtherSpellEffect,
        DebuffSelfSpellEffect,
        TeleportSelfSpellEffect,
        TeleportOtherSpellEffect
    ] = Field(...,description="The effect of the spell.")
    description: str = Field(...,description="A description of the spell effect. Should be at least a sentence long.", min_length=1)
    skill_level_required: str = Field(...,description="The level of skill required to use the weapon. Novice:0, Apprentice: 20, Journeyman: 40, Expert: 60, Master: 80", examples=[
        "novice",
        "apprentice",
        "journeyman",
        "expert",
        "master"
    ], pattern="^(novice|apprentice|journeyman|expert|master)$")
