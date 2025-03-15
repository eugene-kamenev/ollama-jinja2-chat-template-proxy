## Ollama Chat Template proxy for Jinja2

Having issues using Ollama Model chat templates? Here is one of the possible solution.

If you want to use Jinja2 chat templates with Ollama, you can start a proxy behind Ollama.
Handle `/api/chat` enpodint requests, render templates, then proxy will use `/api/generate` with `raw: true` to get model response and bypass Ollama chat template engine. If you want you can also handle tool calls from the model. Right now proxy supports same tool calling parsing in [default.py](templates/default.py) plugin example. Streaming with tool calling is also supported.
