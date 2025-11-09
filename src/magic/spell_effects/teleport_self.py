from pydantic import BaseModel, Field
from typing import Union

from .base_spell_effect import BaseSpellEffect

class TeleportSelfSpellEffect(BaseSpellEffect):
    """Teleport Spell Effect Schema - A teleport effect of a spell in a text adventure game. All fields are required to have a value."""
    type_string: str = Field(description="The type of spell effect.", pattern="^TeleportSelf$")
    location: str = Field(...,description="The location that the spell teleports the caster to.", min_length=1)
