from pydantic import BaseModel, Field
from typing import Union

from .base_spell_effect import BaseSpellEffect

class BuffSelfSpellEffect(BaseSpellEffect):
    """Buff Spell Effect Schema - A buff effect of a spell in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of spell effect.", pattern="^BuffSelf$")
    stat_buffed: str = Field(...,description="The stat that is buffed by the spell effect.", examples=["Strength","Intelligence","Agility","Charisma","Endurance","Perception","Luck"])
    buff_amount: int = Field(...,description="The amount of buff applied by the spell effect.", ge=1,le=10)
