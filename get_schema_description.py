# import json
def get_schema_description(schema):
    schema_description = ""
    # print("Schema:", json.dumps(schema, indent=2))
    if "description" in schema and schema["description"] is not None:
        schema_description += schema["description"]
    def parse_property(property,schema_description):
        if type(property) == dict:
            if "title" in property and property["title"] is not None:
                description_part = property["title"] + ": "
            else:
                description_part = ""
            add_to_description = False
            if "description" in property and property["description"] is not None and "title" in property and property["title"] is not None:
                description_part += property["description"]
                add_to_description = True
            if "examples" in property and property["examples"] is not None and type(property["examples"]) == list[str]:
                description_part += "\nExamples: " + ", ".join(property["examples"])
                add_to_description = True
            if "$ref" in property:
                reference = schema["$defs"][property["$ref"].split("/")[-1]]
                if "title" in reference and reference["title"] is not None:
                    description_part += reference["title"] + ": "
                    add_to_description = True   
                if "description" in reference and reference["description"] is not None:
                    description_part += reference["description"]
                    add_to_description = True
                if "examples" in reference and reference["examples"] is not None:
                    description_part += "\nExamples: " + ", ".join(reference["examples"])
                    add_to_description = True
                if "properties" in reference and reference["properties"] is not None:
                    for sub_key in reference["properties"]:
                        # print("Sub Key:", sub_key)
                        description_part = parse_property(reference["properties"][sub_key],description_part)
                        add_to_description = True
            if "items" in property and property["items"] is not None:
                if "$ref" in property["items"]:
                    if "$def" in schema and schema["$defs"] is not None:
                        reference = schema["$defs"][property["items"]["$ref"].split("/")[-1]]
                        # if "title" in reference and reference["title"] is not None:
                        #     description_part += "\n" + reference["title"] + ": "
                        if "description" in reference and reference["description"] is not None:
                            description_part += reference["description"]
                            add_to_description = True
                        if "examples" in reference and reference["examples"] is not None:
                            description_part += "\nExamples: " + ", ".join(reference["examples"])
                            add_to_description = True
                        if "properties" in reference and reference["properties"] is not None:
                            for sub_key in reference["properties"]:
                                # print("Sub Key:", sub_key)
                                description_part = parse_property(reference["properties"][sub_key],description_part)
                                add_to_description = True
            if "anyOf" in property and property["anyOf"] is not None:
                for sub_property in property["anyOf"]:
                    if "$ref" in sub_property:
                        reference = schema["$defs"][sub_property["$ref"].split("/")[-1]]
                        # if "title" in reference and reference["title"] is not None:
                        #     description_part += "\n" + reference["title"] + ": "
                        description_part += "\n\n"
                        if "description" in reference and reference["description"] is not None:
                            description_part += reference["description"]
                            add_to_description = True
                        if "examples" in reference and reference["examples"] is not None:
                            description_part += "\nExamples: " + ", ".join(reference["examples"])
                            add_to_description = True
                        if "properties" in reference and reference["properties"] is not None:
                            for sub_key in reference["properties"]:
                                # print("Sub Key:", sub_key)
                                description_part = parse_property(reference["properties"][sub_key],description_part)
                                add_to_description = True
            if "properties" in property and property["properties"] is not None:
                for sub_key in property["properties"]:
                    # print("Sub Key:", sub_key)
                    description_part = parse_property(property["properties"][sub_key],description_part)
                    add_to_description = True
            if add_to_description:
                schema_description += "\n" + description_part
        return schema_description
    for key in schema["properties"]:
        # print("Key:", key)
        # print("Value:", character_card_schema[key])
        schema_description = parse_property(schema["properties"][key],schema_description)
    # if "$defs" in schema and schema["$defs"] is not None:
    #     for key in schema["$defs"]:
    #         sub_schema = schema["$defs"][key]
            # sub_schema_description = get_schema_description(sub_schema)
            # schema_description += "\n" + sub_schema_description
    return schema_description

def pydantic_to_open_router_schema(schema, disallowed_keys = []): # ["minLength", "maxLength", "minItems", "maxItems"] for openrouter
    """Convert the schema to the OpenRouter format."""
    # Convert the schema to the OpenRouter format
    def parse_schema_part(schema_part, nested=True):
        if nested:
            parsed_schema = {}
        else:
            parsed_schema = {
                "strict": True,
                "schema":{}
            }
        for key, value in schema_part.items():
            if key in disallowed_keys:
                continue
            if key == "title" or key == "name":
                parsed_schema["name"] = value
            elif key == "properties":
                if nested:
                    parsed_schema["properties"] = {}
                else:
                    parsed_schema["schema"]["properties"] = {}
                for sub_key, sub_value in value.items():
                    if nested:
                        parsed_schema["properties"][sub_key] = parse_schema_part(sub_value)
                    else:
                        parsed_schema["schema"]["properties"][sub_key] = parse_schema_part(sub_value)
            elif key == "$defs":
                if nested:
                    parsed_schema["$defs"] = {}
                else:
                    parsed_schema["schema"]["$defs"] = {}
                for sub_key, sub_value in value.items():
                    if nested:
                        parsed_schema["$defs"][sub_key] = parse_schema_part(sub_value)
                    else:
                        parsed_schema["schema"]["$defs"][sub_key] = parse_schema_part(sub_value)
            else:
                if nested:
                    parsed_schema[key] = value
                else:
                    parsed_schema["schema"][key] = value
        return parsed_schema
    return parse_schema_part(schema, False)

def openrouter_to_pydantic_schema(schema):
    """Convert the OpenRouter schema to Pydantic schema."""
    def parse_schema_part(schema_part):
        parsed_schema = {}
        for key, value in schema_part.items():
            if key == "name":
                parsed_schema["title"] = value
            elif key == "properties":
                parsed_schema["properties"] = {}
                for sub_key, sub_value in value.items():
                    parsed_schema["properties"][sub_key] = parse_schema_part(sub_value)
            elif key == "$defs":
                parsed_schema["$defs"] = {}
                for sub_key, sub_value in value.items():
                    parsed_schema["$defs"][sub_key] = parse_schema_part(sub_value)
            else:
                parsed_schema[key] = value
        return parsed_schema
    return parse_schema_part(schema)