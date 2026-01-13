import copy
from typing import Any, Dict

# Fields that Gemini's schema validation doesn't support
GEMINI_UNSUPPORTED_FIELDS = {
    "title",
    "description",
    "examples",
    "default",
    "$schema",
    "additionalProperties",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "pattern",
    "format",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minItems",
    "maxItems",
    "uniqueItems",
}


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


def remove_unsupported_fields(schema: Any) -> Any:
    """Recursively remove fields that Gemini doesn't support in schemas"""
    if isinstance(schema, dict):
        result = {}
        for key, value in schema.items():
            if key in GEMINI_UNSUPPORTED_FIELDS:
                continue
            result[key] = remove_unsupported_fields(value)
        return result
    elif isinstance(schema, list):
        return [remove_unsupported_fields(item) for item in schema]
    else:
        return schema


def clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a JSON schema to be compatible with Gemini's structured output"""
    schema = copy.deepcopy(schema)
    
    # Step 1: Inline $refs
    defs = schema.pop("$defs", {})
    if defs:
        schema = inline_refs(schema, defs)
    
    # Step 2: Remove unsupported fields
    schema = remove_unsupported_fields(schema)
    
    return schema
