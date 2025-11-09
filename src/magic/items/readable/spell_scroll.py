from pydantic import BaseModel, Field
from typing import Union

from src.regex_patterns import lower_single_sentence
from src.magic import Spell
from src.items import Item

class SpellScroll(Item):
    """Spell Scroll Schema - A spell scroll item in a text adventure game. All fields are required to have a value. Spell scrolls can be used by characters to cast a single spell. Spell scrolls can have different effects, such as damage, healing, buffs, debuffs, etc."""
    type_string: str = Field(description="The type of item.", pattern="^SpellScroll$")
    physical_description: str = Field(description="A physical description of the spell scroll that only describes the item itself. It should not describe it's relation to the area/people it's nearby, on or around. Should be at least a sentence long.", min_length=1, examples=[
        "a rolled-up parchment with ancient runes inscribed on it, tied with a red ribbon",
        "a weathered scroll made of papyrus, sealed with a wax emblem",
        "a delicate scroll made of fine silk, adorned with intricate patterns and symbols",
        "a sturdy scroll made of thick vellum, bound with leather straps",
        "a magical scroll that glows with a faint blue light, inscribed with arcane symbols",
    ], pattern=lower_single_sentence)
    spell: Spell = Field(...,description="The spell contained in the scroll.")
