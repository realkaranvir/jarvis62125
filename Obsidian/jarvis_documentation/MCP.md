#### Custom MCP Server based on Anthropic Docs
- Uses a simple `MCP server` in `python`
- Uses a `Quart server` as a proxy for communication between the `STDIO` MCP interactions and http requests
#### Installation
```
cd mcp-proxy/mcp-server
source .venv/bin/activate
uv sync
deactivate
cd ..
source .venv/bin/activate
uv sync
```
#### Running
```
cd mcp-proxy
source .venv/bin/activate
python main.py
```