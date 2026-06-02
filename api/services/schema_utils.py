import copy
from typing import Any, Dict

# Simple fields that can be removed without breaking the schema
JSON_SCHEMA_REMOVABLE_FIELDS = {
    "title",
    "description",
    "examples",
    "default",
    "$schema",
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
    "const",
    "contentMediaType",
    "contentEncoding",
    "if",
    "then",
    "else",
    "not",
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


def simplify_union_types(schema: Any) -> Any:
    """
    Simplify anyOf/oneOf constructs:
    - For Optional types (anyOf with null), extract the non-null type
    - For other unions, take the first option
    """
    if isinstance(schema, dict):
        # Handle anyOf (Pydantic uses this for Optional types)
        if "anyOf" in schema:
            options = schema["anyOf"]
            # Filter out null types
            non_null_options = [
                opt for opt in options
                if not (isinstance(opt, dict) and opt.get("type") == "null")
            ]
            
            if len(non_null_options) == 1:
                # Optional field - use the non-null type
                result = simplify_union_types(non_null_options[0])
            elif len(non_null_options) > 1:
                # Union type - take the first option
                result = simplify_union_types(non_null_options[0])
            else:
                # Only null options - make it a string
                result = {"type": "string"}
            
            # Preserve other fields from the original schema
            for key, value in schema.items():
                if key != "anyOf" and key not in result:
                    result[key] = simplify_union_types(value)
            
            return result
        
        # Handle oneOf similarly
        if "oneOf" in schema:
            options = schema["oneOf"]
            non_null_options = [
                opt for opt in options
                if not (isinstance(opt, dict) and opt.get("type") == "null")
            ]
            
            if non_null_options:
                result = simplify_union_types(non_null_options[0])
            else:
                result = {"type": "string"}
            
            for key, value in schema.items():
                if key != "oneOf" and key not in result:
                    result[key] = simplify_union_types(value)
            
            return result
        
        # Handle allOf by merging all schemas
        if "allOf" in schema:
            merged = {}
            for sub_schema in schema["allOf"]:
                simplified = simplify_union_types(sub_schema)
                if isinstance(simplified, dict):
                    merged.update(simplified)
            
            for key, value in schema.items():
                if key != "allOf":
                    merged[key] = simplify_union_types(value)
            
            return merged
        
        # Regular object - process recursively
        result = {}
        for key, value in schema.items():
            result[key] = simplify_union_types(value)
        return result
    
    elif isinstance(schema, list):
        return [simplify_union_types(item) for item in schema]
    else:
        return schema


def remove_unsupported_fields(schema: Any, is_inside_properties: bool = False) -> Any:
    """
    Recursively remove fields that lightweight JSON-mode providers often reject.
    
    NOTE: Only remove annotation fields (like 'title', 'description') when they are
    schema annotations, NOT when they are actual property names inside 'properties'.
    """
    if isinstance(schema, dict):
        result = {}
        for key, value in schema.items():
            # If we're inside "properties", keys are field NAMES - never remove them
            if is_inside_properties:
                # Process nested values, but mark we're no longer directly in properties
                result[key] = remove_unsupported_fields(value, is_inside_properties=False)
            else:
                # We're at schema level - here 'title', 'description' are annotations to remove
                if key in JSON_SCHEMA_REMOVABLE_FIELDS:
                    continue
                # additionalProperties should be removed
                if key == "additionalProperties":
                    continue
                # When entering "properties", mark that keys are field names
                if key == "properties":
                    result[key] = remove_unsupported_fields(value, is_inside_properties=True)
                else:
                    result[key] = remove_unsupported_fields(value, is_inside_properties=False)
        return result
    elif isinstance(schema, list):
        return [remove_unsupported_fields(item, is_inside_properties=False) for item in schema]
    else:
        return schema


def fix_required_fields(schema: Any) -> Any:
    """Remove required fields that reference non-existent properties"""
    if isinstance(schema, dict):
        result = {}
        for key, value in schema.items():
            result[key] = fix_required_fields(value)
        
        # If this is an object type with required fields, validate them
        if result.get("type") == "object" and "required" in result:
            properties = result.get("properties", {})
            valid_required = [
                field for field in result["required"]
                if field in properties
            ]
            if valid_required:
                result["required"] = valid_required
            else:
                # Remove empty required array
                del result["required"]
        
        return result
    elif isinstance(schema, list):
        return [fix_required_fields(item) for item in schema]
    else:
        return schema


def fix_empty_objects(schema: Any) -> Any:
    """
    Fix OBJECT types with empty properties.
    Some structured-output providers reject empty OBJECT schemas.
    Convert them to string type or add a placeholder.
    """
    if isinstance(schema, dict):
        result = {}
        for key, value in schema.items():
            result[key] = fix_empty_objects(value)
        
        # If this is an object type, ensure it has properties
        if result.get("type") == "object":
            properties = result.get("properties", {})
            if not properties or len(properties) == 0:
                # Convert empty object to a simple string type
                # This handles things like Dict[str, Any] which schema-constrained providers can't handle
                return {"type": "string"}
        
        return result
    elif isinstance(schema, list):
        return [fix_empty_objects(item) for item in schema]
    else:
        return schema


def clean_schema_for_llm(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a JSON schema for compact prompt/schema guidance."""
    schema = copy.deepcopy(schema)
    
    # Step 1: Inline $refs
    defs = schema.pop("$defs", {})
    if defs:
        schema = inline_refs(schema, defs)
    
    # Step 2: Simplify union types (anyOf, oneOf, allOf)
    schema = simplify_union_types(schema)
    
    # Step 3: Remove unsupported fields
    schema = remove_unsupported_fields(schema)
    
    # Step 4: Fix required fields that reference non-existent properties
    schema = fix_required_fields(schema)
    
    # Step 5: Fix empty OBJECT types
    schema = fix_empty_objects(schema)
    
    return schema


# Backwards-compatible alias for older imports/tests.
def clean_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
    return clean_schema_for_llm(schema)
