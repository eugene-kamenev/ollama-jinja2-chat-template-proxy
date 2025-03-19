import templates.default as d

def hook(data):
    data['add_generation_prompt'] = True
    return data

def parse_tool_calls(str):
    return d.parse_tool_calls(str)
