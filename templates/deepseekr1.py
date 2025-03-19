import templates.default as d

def hook(data):
    data['add_generation_prompt'] = True
    data['bos_token'] = '<｜begin▁of▁sentence｜>'
    data['eos_token'] = '<｜end▁of▁sentence｜>'
    return data

def parse_tool_calls(str):
    return d.parse_tool_calls(str)
