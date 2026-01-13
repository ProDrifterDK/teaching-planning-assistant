import copy
from typing import Any, Dict


def inline_refs(schema: Dict[str, Any], defs: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(schema, dict):
        if "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/$defs/"):
                def_name = ref_path.split("/")[-1]
                if def_name in defs:
                    inlined = copy.deepcopy(defs[def_name])
                    return inline_refs(inlined, defs)
            return schema
        
        result = {}
        for key, value in schema.items():
            if key == "$defs":
                continue
            result[key] = inline_refs(value, defs)
        return result
    elif isinstance(schema, list):
        return [inline_refs(item, defs) for item in schema]
    else:
        return schema


def clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    schema = copy.deepcopy(schema)
    
    defs = schema.pop("$defs", {})
    
    if defs:
        schema = inline_refs(schema, defs)
    
    return schema
