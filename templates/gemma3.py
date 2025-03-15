import templates.default as d

def hook(data):
    data['add_generation_prompt'] = True
    data['bos_token'] = '<bos>'
    return data

def parse_tool_calls(str):
    return d.parse_tool_calls(str)
