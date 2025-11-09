from pydantic import BaseModel, Field
from typing import Union

from .base_spell_effect import BaseSpellEffect

class DebuffOtherSpellEffect(BaseSpellEffect):
    """Debuff Spell Effect Schema - A debuff effect of a spell in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of spell effect.", pattern="^DebuffOther$")
    stat_debuffed: str = Field(...,description="The stat that is debuffed by the spell effect.", examples=["Strength","Intelligence","Agility","Charisma","Endurance","Perception","Luck"])
    debuff_amount: int = Field(...,description="The amount of debuff applied by the spell effect.", ge=1,le=10)
