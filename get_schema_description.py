def get_schema_description(schema):
    schema_description = ""
    # print("Schema:", schema)
    if "description" in schema and schema["description"] is not None:
        schema_description += schema["description"]
    for key in schema["properties"]:
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
                if "examples" in property and property["examples"] is not None:
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
                if "properties" in property and property["properties"] is not None:
                    for sub_key in property["properties"]:
                        # print("Sub Key:", sub_key)
                        description_part = parse_property(property["properties"][sub_key],description_part)
                        add_to_description = True
                if add_to_description:
                    schema_description += "\n" + description_part
            return schema_description
        # print("Key:", key)
        # print("Value:", character_card_schema[key])
        schema_description = parse_property(schema["properties"][key],schema_description)
    return schema_description