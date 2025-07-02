import sys
import signal
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

import utils

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

from quart import Quart, request, jsonify
from quart_cors import cors

import ollama

load_dotenv() # Load environment variables from .env

# TODO: encapsulate LLM client to enable easy switching between different LLMs
# TODO: refactor code to be more modular and maintainable

class AnthropicAPI:
    def __init__(self):
        self.anthropic = Anthropic()
        self.context_len = 128000
        self.response_limit = self.context_len // 20

    def query_llm(self, messages: list, tools: list, system_prompt: str):
        """Query the Anthropic LLM with given messages and tools"""
        # Structure tools for Anthropic API
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in tools]

        response = self.anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            messages=messages,
            tools=available_tools,
            system=system_prompt
        )
        tool_calls = []
        llm_response = ""
        for content in response.content:
            if content.type == 'text':
                llm_response = content.text
            else:
                tool_calls.append({'name': content.name, 'args': content.input, 'tool_use_id': content.id})
        result = {'llm_response': llm_response, 'tool_calls': tool_calls}
        return result
    
    def format_tool_call(self, tool_use_id, tool_name, tool_args):
        tool_call = {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tool_use_id,
                                "name": tool_name,
                                "input": tool_args
                            }
                        ]
                    }
        return tool_call
    def format_tool_result(self, tool_use_id, result):
        tool_result = {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result
                            }
                        ]
                    }
        return tool_result

class OllamaAPI:
    def __init__(self):
        self.model = 'jarvis-qwen3:latest'
        self.context_len = 40000
        self.response_limit = self.context_len // 4
        self.tool_use_id_counter = 0
        load_result = {'done': False}
        try:
            print(f"trying to load model: {self.model}")
            load_result = ollama.chat(model=self.model, keep_alive="24h")
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print("pulling model")
                ollama.pull(self.model)
                load_result = ollama.chat(model=self.model, keep_alive="24h")
        if (load_result['done'] != True):
            print(f'Error loading model: {self.model}')

    def query_llm(self, messages: list, tools: list, system_prompt: str):
        """Query the local ollama LLM with given messages and tools"""
        self.tool_use_id_counter += 1
        if self.tool_use_id_counter > 10000:
            self.tool_use_id_counter = 1

        # Structure tools for Ollama
        available_tools = [{
            'type': 'function',
            'function': {
                'name': tool.name,
                'description': tool.description,
                'parameters': {
                    'type': tool.inputSchema['type'],
                    'required': tool.inputSchema['required'],
                    'properties': tool.inputSchema['properties']
                }
            }
        } for tool in tools]

        response = ollama.chat(model=self.model, think=False, messages=messages, tools=available_tools)
        print(f"\nresponse: {response}\n")
        tool_calls = []
        if response.message.tool_calls:
            tool_calls = [{'name': tool.function.name, 'args': tool.function.arguments, 'tool_use_id': str(self.tool_use_id_counter) } for tool in response.message.tool_calls]
        # Sometimes model returns tool call in content message
        if response.message.content and response.message.content[:13] == 'type=tool_use':
            info = utils.parse_tool_string()
            tool_calls.append({'name': info['name'], 'args': info['input'], 'tool_use_id': info['id']})
        else:
            llm_response = response.message.content
        result = {'llm_response': llm_response, 'tool_calls': tool_calls}
        print(f"\n{result}\n")
        return result

    def format_tool_call(self, tool_use_id, tool_name, tool_args):
        tool_call = {
                        "role": "assistant",
                        "content": utils.stringify([
                            {
                                "type": "tool_use",
                                "id": tool_use_id,
                                "name": tool_name,
                                "input": utils.stringify(tool_args)
                            }
                        ])
                    }
        return tool_call
    def format_tool_result(self, tool_use_id, result):
        tool_result = {
                        "role": "user",
                        "content": utils.stringify([
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result
                            }
                        ])
                    }
        return tool_result

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack() # Handles closing of async resources
        self.llm = OllamaAPI()
    # methods will go here
    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
        
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str, messages: list[dict]) -> dict:
        """Process a query using Claude and available tools"""
        NAME = "Jarvis"
        SYSTEM_PROMPT = f"Your name is {NAME}. You are a formal, concise assistant who always refers to the user as sir. You answer in no more than two sentences. Do not ask follow-up questions unless absolutely necessary to understand the current query. Do not offer additional information, suggestions, or clarifications unless directly requested. You are helpful but reserved. If a question cannot be answered without more information, state that clearly and wait for further input. You have access to tools, but you will only use them when the question cannot be answered directly."

        if messages is None:
            messages = []
        messages.append({
                "role": "user",
                "content": query
        })
        # List available tools for the LLMeturn
        available_tools = (await self.session.list_tools()).tools

        # Initial LLM call
        response = self.llm.query_llm(
            messages=messages,
            tools=available_tools,
            system_prompt=SYSTEM_PROMPT
        )

        llm_response = response['llm_response']

        messages.append({
            'role': 'assistant',
            'content': llm_response
        })

        tool_calls = response['tool_calls']
        num_tool_calls_left = len(tool_calls)

        while (num_tool_calls_left > 0):
            for tool_call in tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_use_id = tool_call['tool_use_id']

                result = await self.session.call_tool(tool_name, tool_args)
                print(f"\nTool result: {utils.cap_start(result.content[0].text, self.llm.response_limit)}\n")
                tool_call = self.llm.format_tool_call(tool_use_id, tool_name, tool_args)
                tool_result = self.llm.format_tool_result(tool_use_id, utils.cap_start(result.content[0].text, self.llm.response_limit))

                messages.extend([tool_call, tool_result])
                num_tool_calls_left -= 1

            response = self.llm.query_llm(
                messages=messages,
                tools=available_tools,
                system_prompt=SYSTEM_PROMPT
            )

            llm_response = response['llm_response']
            messages.append({
                'role': 'assistant',
                'content': llm_response
            })
            tool_calls = response['tool_calls']
            num_tool_calls_left = len(tool_calls)

        return_object = {
            'history': messages,
            'LLM_response': llm_response
        }
        return return_object

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

client = MCPClient()

async def connect_to_server():
    try:
        await client.connect_to_server("mcp-server/server.py")
    except Exception as e:
        print(f"Error connecting to server: {str(e)}")
        sys.exit(1)

# Create Flask app
app = Quart(__name__)
app = cors(app, allow_origin="*") # TODO: Change to certain origins later, also do for speaches server

@app.before_serving
async def startup():
    """Start the server connection before serving requests"""
    await connect_to_server()

@app.after_serving
async def shutdown():
    """Clean up resources after serving requests"""
    print("Shutting down server gracefully...")
    await client.cleanup()

# Register signal handler to handle SIGINT (Ctrl+C)
def signal_handler(sig, frame):
    """Handle SIGINT gracefully."""
    asyncio.create_task(shutdown())  # Schedule the shutdown task

# Register the signal handler to capture Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/query', methods=['POST'])
async def query_llm():
    """Endpoint to query the LLM"""
    req_body = await request.get_json()
    query = req_body.get('query')
    history = req_body.get('history', [])
    if not isinstance(history, list):
        return jsonify({'error': 'Invalid history format'}), 400
    # Validate history items
    for item in history:
        if not isinstance(item, dict) or 'role' not in item or 'content' not in item:
            return jsonify({'error': 'Invalid history item format'}), 400
        if item['role'] not in ['user', 'assistant', 'system']:
            return jsonify({'error': 'Invalid role in history item'}), 400
    try:
        if not query or not isinstance(query, str) or len(query) == 0 or len(query) > 1000:
            return jsonify({'error': 'Invalid query'}), 400
        response = await client.process_query(query, history)
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(use_reloader=False, debug=True) # TODO: change