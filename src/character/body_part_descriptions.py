from pydantic import BaseModel, Field

class BodyPartDescriptions(BaseModel):
    """Body Part Descriptions Schema - A set of descriptions for a character's body parts. Should not describe their clothes or equipment in any way. The descriptions are intended to be combined into a single description with linebreaks between each part in the final output, so write them such that they should cohesively flow together, seperated by new lines, and not repeat themselves. All fields are required to have a value. Body part descriptions should only use the characters gender to refer to them, never by name. Example: \"She has a cute face.\" Additionally, NEVER mention what the NPC is wearing when describing their body parts. All clothing MUST be an WornClothing item."""
    hair_description: str = Field(...,description="A description of the character's hair. Should be at least a paragraph long and explicitly and graphically describe the character's hair.", min_length=1, examples=[
        "She has long, flowing, blonde hair that cascades down her back in gentle waves."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    face_description: str = Field(...,description="A description of the character's face. Should be at least a paragraph long and explicitly and graphically describe the character's nude face.", min_length=1, examples=[
        "She has a cute face with big, bright eyes and a small, upturned nose."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    naked_upper_body_description: str = Field(...,description="A description of the character's chest without clothes. Should be at least a paragraph long and explicitly and graphically describe the character's nude chest.", min_length=1, examples=[
        "She has a perky pair of breasts with small, pink nipples that stand out against her pale skin."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    abdomen_description: str = Field(...,description="A description of the character's abdomen not including the chest or genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude body.", min_length=1, examples=[
        "Her abdomen is flat and toned, with a small belly button in the center."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    naked_genital_description: str = Field(...,description="A description of the character's genitals. Should be at least a paragraph long and explicitly and graphically describe the character's nude genitals.", min_length=1, examples=[
        "She has a small, neatly trimmed bush of pubic hair above her pussy, which is small and tight."
    ], pattern="^(His|Her|He|She|Between)([A-Za-z0-9 ])*$")
    butt_description: str = Field(...,description="A description of the character's butt. Should be at least a paragraph long and explicitly and graphically describe the character's nude butt.", min_length=1, examples=[
        "She has a perky, round butt that looks great in a pair of tight jeans."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    legs_description: str = Field(...,description="A description of the character's legs. Should be at least a paragraph long and explicitly and graphically describe the character's nude legs.", min_length=1, examples=[
        "She has long, toned legs that look great in a pair of shorts."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    arms_description: str = Field(...,description="A description of the character's arms. Should be at least a paragraph long and explicitly and graphically describe the character's nude arms.", min_length=1, examples=[
        "She has long, slender arms with delicate hands and long fingers."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    hands_description: str = Field(...,description="A description of the character's hands. Should be at least a paragraph long and explicitly and graphically describe the character's nude hands.", min_length=1, examples=[
        "She has small, delicate hands with long fingers and neatly trimmed nails."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")
    feet_description: str = Field(...,description="A description of the character's feet. Should be at least a paragraph long and explicitly and graphically describe the character's nude feet.", min_length=1, examples=[
        "She has small, dainty feet with high arches and neatly painted toenails."
    ], pattern="^(His|Her|He|She)([A-Za-z0-9 ])*$")

    def to_json(self):
        return {
            "hair_description": self.hair_description,
            "face_description": self.face_description,
            "naked_upper_body_description": self.naked_upper_body_description,
            "abdomen_description": self.abdomen_description,
            "naked_genital_description": self.naked_genital_description,
            "butt_description": self.butt_description,
            "legs_description": self.legs_description,
            "arms_description": self.arms_description,
            "hands_description": self.hands_description,
            "feet_description": self.feet_description
        }

    @staticmethod
    def from_json(data: dict):
        return BodyPartDescriptions(**data)