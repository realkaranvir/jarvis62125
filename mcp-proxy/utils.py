import re

def flatten_json(obj, parent_key='', sep='.'):
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(flatten_json(v, new_key, sep=sep))
            elif isinstance(v, list):
                if all(not isinstance(i, (dict, list)) for i in v):
                    items[new_key] = ','.join(map(str, v))
                else:
                    for i, item in enumerate(v):
                        items.update(flatten_json({str(i): item}, new_key, sep=sep))
            else:
                items[new_key] = v
    return items

def stringify(obj):
    if isinstance(obj, dict):
        flat = flatten_json(obj)
        return ', '.join(f"{k}={v}" for k, v in flat.items())
    elif isinstance(obj, list):
        return ','.join([stringify(item) for item in obj])
    else:
        raise ValueError("Expected a dict or a list of dicts.")
    
def parse_tool_string(tool_string):
    # Match the outer structure
    pattern = r"type=(\w+), id=(\d+), name=([\w_]+), input=\s*(.+)"
    match = re.match(pattern, tool_string.strip())
    
    if not match:
        raise ValueError("Input string is not in the expected format.")
    
    tool_type, tool_id, tool_name, input_raw = match.groups()

    # Split on commas or spaces, ignore empty parts
    input_parts = re.split(r"[,\s]+", input_raw.strip())
    
    # Parse key=value pairs
    input_data = {}
    for part in input_parts:
        if "=" in part:
            key, value = part.split("=", 1)
            input_data[key.strip()] = value.strip()

    return {
        "type": tool_type,
        "id": tool_id,
        "name": tool_name,
        "input": input_data
    }

def cap_start(s, limit):
    return s if len(s) <= limit else s[:limit - 3] + "...and more"

def cap_end(s, limit):
    return s if len(s) <= limit else "..." + s[-(limit - 3):]
