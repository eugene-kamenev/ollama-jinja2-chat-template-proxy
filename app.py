import logging
import json
import requests
from jinja2 import Template, Environment, FileSystemLoader
from flask import Flask, request, Response


MASTER_SERVER = "http://ollama:11434"

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
env = Environment(loader=FileSystemLoader("templates"))
TEMPLATES = {}

def load_plugin(model):
    try:
        plugin = __import__(f"templates.{model}", fromlist=[""])
        logger.info(f"Loaded plugin for model {model}")
        return plugin
    except Exception as e:
        logger.error(f"Unable to find plugin for model {model}")
        
DEFAULT_PLUGIN = load_plugin("default")

def reaload_config():
    global TEMPLATES
    TEMPLATES = {}
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        for item in config:
            try:
                template = env.get_template(item['template'])
                plugin = load_plugin(item.get("plugin")) if item.get("plugin") is not None else None
                for model in item['models']:
                    TEMPLATES[model] = {"template": template, "plugin": plugin}
            except Exception as e:
                logger.error(f"Error loading template. {e}")
                
def copy(a, b, keys = []):
    for key, value in a.items():
        if value is not None and (len(keys) == 0 or key in keys):
            b[key] = value

def handle_chat_request(data, config):
    try:
        template = config.get("template")
        plugin = config.get("plugin") or DEFAULT_PLUGIN
        if data.get("jinja_template"):
            template = Template(data.get('jinja_template'))
        data = plugin.hook(data)
        return template.render(data) if template else None
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    
@app.route("/<path:endpoint>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy_request(endpoint):
    if endpoint == 'reload':
        reaload_config()
        return Response("{\"status\": \"OK\"}", status=200)
    
    try:
        is_streaming = True
        incoming_data = request.json if request.method in ["POST", "PUT"] else None
        
        if request.method in ["POST", "PUT"] and incoming_data:
            is_streaming = incoming_data.get("stream", True)
        
        new_body = None
        
        config = TEMPLATES.get(incoming_data.get('model'), {}) if incoming_data and endpoint == 'api/chat' else {}
        
        if endpoint == 'api/chat':
            logger.info(f"Incoming request to: {endpoint}")
            logger.info(f"Request Body: {incoming_data}")
            raw_request = handle_chat_request(incoming_data, config)
            if raw_request:
                new_body = {
                    "raw"       : True,
                    "prompt"    : raw_request
                }
                copy(incoming_data, new_body, ['model', 'format', 'keep_alive', 'options', 'stream'])
                logger.info(f"Modified request: {new_body}")
                endpoint = 'api/generate'
        
        url = f"{MASTER_SERVER}/{endpoint}"
        response = requests.request(
            method=request.method,
            url=url,
            json=new_body or incoming_data,
            params=request.args,
            headers={key: value for key, value in request.headers if key.lower() != "host"},
            stream=is_streaming
        )

        headers = {key: value for key, value in response.headers.items() if key.lower() not in ["transfer-encoding", "content-encoding"]}
        
        def generate():
            message = ""
            next_allowed = True
            for chunk in response.iter_lines():
                if chunk:
                    line = chunk.decode("utf-8")
                    if new_body is not None and incoming_data is not None:
                        chunk_message = json.loads(line)
                        model_response = chunk_message.pop('response', "")
                        chunk_message["message"] = {
                            "role": "assistant",
                            "content": model_response
                        }
                        message += model_response
                        if incoming_data.get("tools") is not None:
                            plugin = config.get("plugin") or DEFAULT_PLUGIN
                            tools = plugin.parse_tool_calls(message)
                            if len(tools) > 0:
                                chunk_message['done'] = True
                                chunk_message['done_reason'] = "tool_call"
                                chunk_message['total_duration'] = 0
                                chunk_message['load_duration'] = 0
                                chunk_message["prompt_eval_count"] = 0
                                chunk_message["prompt_eval_duration"] = 0
                                chunk_message["eval_count"] = 0
                                chunk_message["eval_duration"] = 0
                                chunk_message["message"]['content'] = ""
                                chunk_message["message"]["tool_calls"] = tools
                                next_allowed = False
                                
                        line = json.dumps(chunk_message, ensure_ascii=False)
                    yield line + "\n"
                    if not next_allowed:
                        return
                                
        content = None if is_streaming else response.content
        if not is_streaming and new_body is not None:
            try:
                ollama_response = json.loads(content)
                model_response = ollama_response.pop('response', "")
                ollama_response['message'] = {
                    "role": "assistant",
                    "content": model_response
                }
                logger.info(f"Model response: {model_response}")
                if incoming_data.get("tools"):
                    plugin = config.get("plugin") or DEFAULT_PLUGIN
                    tools = plugin.parse_tool_calls(model_response)
                    if len(tools) > 0:
                        ollama_response['done_reason'] = "tool_call"
                        ollama_response['message']["tool_calls"] = tools
                        ollama_response['message']["content"] = ""
                content = json.dumps(ollama_response, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error: {e}")

        return Response(generate() if is_streaming else content,
                        status=response.status_code, 
                        headers=response.headers)
    
    except Exception as e:
        return Response(str(e), status=500)

if __name__ == "__main__":
    reaload_config()
    app.run(host="0.0.0.0", port=5000)
