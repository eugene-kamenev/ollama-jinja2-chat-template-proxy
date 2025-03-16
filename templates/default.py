import json
import re

def parse_tool_calls(str):
    """
    Extracts JSON objects that match the structure:
    {"name": "...", "arguments": {...}}
    """
    pattern = r'(\{\s*(?:(?:"name"|name)\s*:\s*".+?"\s*,\s*(?:"arguments"|arguments)\s*:\s*\{.*?\}|(?:"arguments"|arguments)\s*:\s*\{.*?\}\s*,\s*(?:"name"|name)\s*:\s*".+?")\s*\})'

    matches = re.findall(pattern, str, re.DOTALL)

    extracted_objects = []
    for match in matches:
        try:
            json_obj = json.loads(match)
            extracted_objects.append({"function": json_obj})
        except json.JSONDecodeError:
            pass

    return extracted_objects

def hook(data):
    # here you can modify the data before template rendering in jinja
    return data
