from pydantic import BaseModel, Field
from typing import Union

from .base_spell_effect import BaseSpellEffect

class DamageSelfSpellEffect(BaseSpellEffect):
    """Damage Spell Effect Schema - A damage effect of a spell in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of spell effect.", pattern="^DamageSelf$")
    damage_amount: int = Field(...,ge=1,description="The amount of damage dealt by the spell effect.")
