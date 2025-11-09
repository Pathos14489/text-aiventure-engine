from pydantic import BaseModel, Field
from typing import Union
from src.items.clothing import Headwear, Footwear, Gloves, LowerBodywear, UpperBodywear, FullBodywear, Accessory, UpperBodyUnderwear, LowerUnderwear

import src.items as Items

class WornClothing(BaseModel):
    """WornClothing Schema - The clothes that a character has on them. This includes all worn clothing, armour and accessories. If the character has no equipment on them, this property should be null."""
    headwear: Union[Headwear,None] = Field(description="The headwear that the character has equiped. If the character has no headwear equiped, this property should be null.")
    fullbodywear: Union[FullBodywear,None] = Field(description="The fullbodywear that the character has equiped. This is only for outfits that cover the entire body. A dress, a jumpsuit, a suit, etc. If the character has no fullbodywear equiped, this property should be null. Multiple clothing items can be used to cover the entire body, so this is not required to be a full outfit. If the character has no fullbodywear equiped, this property should be null.")
    upperbodywear: Union[UpperBodywear,None] = Field(description="The upperbodywear that the character has equiped. If the character has no upperbodywear equiped, this property should be null.")
    upperbody_underwear: Union[UpperBodyUnderwear,None] = Field(description="The underwear that the character has equiped on their upperbody. If the character has no underwear equiped, this property should be null.")
    gloves: Union[Gloves,None] = Field(description="The gloves that the character has equiped. If the character has no gloves equiped, this property should be null.")
    lower_underwear: Union[LowerUnderwear,None] = Field(description="The underwear that the character has equiped. If the character has no underwear equiped, this property should be null.")
    lowerbodywear: Union[LowerBodywear,None] = Field(description="The lowerbodywear that the character has equiped. If the character has no lowerbodywear equiped, this property should be null.")
    footwear: Union[Footwear,None] = Field(description="The footwear that the character has equiped. If the character has no footwear equiped, (e.g. they are bare foot), this property should be null.")
    accessories: list[Accessory] = Field(description="A list of accessories that the character has on them. Each item should have a name, description, value, weight. All items in the location. This can be furniture, or small objects that characters can interact with. If the item is food, it should have a hunger restored and thirst restored value. If the item is a weapon, it should have a damage value and required Attributes. If an item is a weapon, it MUST have a damage value and required Attributes. If an item is food, it MUST have a hunger restored and thirst restored value. This is not worn equipment, but items that the character has in their inventory.")

    def to_json(self):
        return {
            "headwear": self.headwear.to_json() if self.headwear else None,
            "fullbodywear": self.fullbodywear.to_json() if self.fullbodywear else None,
            "upperbodywear": self.upperbodywear.to_json() if self.upperbodywear else None,
            "upperbody_underwear": self.upperbody_underwear.to_json() if self.upperbody_underwear else None,
            "gloves": self.gloves.to_json() if self.gloves else None,
            "lower_underwear": self.lower_underwear.to_json() if self.lower_underwear else None,
            "lowerbodywear": self.lowerbodywear.to_json() if self.lowerbodywear else None,
            "footwear": self.footwear.to_json() if self.footwear else None,
            "accessories": [accessory.to_json() for accessory in self.accessories]
        }
    
    @staticmethod
    def from_json(data: dict):
        data['headwear'] = Items.from_json(data['headwear']) if data.get('headwear') else None
        data['fullbodywear'] = Items.from_json(data['fullbodywear']) if data.get('fullbodywear') else None
        data['upperbodywear'] = Items.from_json(data['upperbodywear']) if data.get('upperbodywear') else None
        data['upperbody_underwear'] = Items.from_json(data['upperbody_underwear']) if data.get('upperbody_underwear') else None
        data['gloves'] = Items.from_json(data['gloves']) if data.get('gloves') else None
        data['lower_underwear'] = Items.from_json(data['lower_underwear']) if data.get('lower_underwear') else None
        data['lowerbodywear'] = Items.from_json(data['lowerbodywear']) if data.get('lowerbodywear') else None
        data['footwear'] = Items.from_json(data['footwear']) if data.get('footwear') else None
        data['accessories'] = [Items.from_json(item) for item in data.get('accessories', [])]
        return WornClothing(**data)