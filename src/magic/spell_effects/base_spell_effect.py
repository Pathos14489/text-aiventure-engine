from pydantic import BaseModel, Field
from typing import Union

class BaseSpellEffect(BaseModel):
    """Spell Effect Schema - An effect of a spell in a text adventure game. All fields are required to have a value. Spell effects can be used to define the effects of a spell when it is cast. Spell effects can have different types, such as damage, healing, buffs, debuffs, etc."""
    type_string: str = Field(description="The type of spell effect.", examples=[
        "DamageOther",
        "DamageSelf",
        "HealOther",
        "HealSelf",
        "BuffOther",
        "BuffSelf",
        "DebuffOther",
        "DebuffSelf",
        "TeleportOther",
        "TeleportSelf",
        "SpawnCharacter",
        "SpawnItem",
        "SpawnNewTravelableLocation"
    ], pattern="^(Damage|Healing|Buff|Debuff|Teleport|SpawnCharacter|SpawnItem|SpawnNewLocation|GivePlayerItem)$")
