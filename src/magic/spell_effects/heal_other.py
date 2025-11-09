from pydantic import BaseModel, Field
from typing import Union

from .base_spell_effect import BaseSpellEffect

class HealOtherSpellEffect(BaseSpellEffect):
    """Heal Spell Effect Schema - A healing effect of a spell in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of spell effect.", pattern="^HealOther$")
    heal_amount: int = Field(...,ge=1,description="The amount of healing done by the spell effect.")
