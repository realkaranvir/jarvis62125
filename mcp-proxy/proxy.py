import sys
import signal
import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

from quart import Quart, request, jsonify
from quart_cors import cors

load_dotenv() # Load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack() # Handles closing of async resources
        self.anthropic = Anthropic()
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

    async def process_query(self, query: str, history: list[dict]) -> dict:
        """Process a query using Claude and available tools"""
        NAME = "Jarvis"
        SYSTEM_PROMPT = f"Your name is {NAME}. You are a formal, concise assistant who always refers to the user as sir. You answer in no more than two sentences. Do not ask follow-up questions unless absolutely necessary to understand the current query. Do not offer additional information, suggestions, or clarifications unless directly requested. You are helpful but reserved. If a question cannot be answered without more information, state that clearly and wait for further input. You have access to tools, but you will only use them when the question cannot be answered directly."

        if history is None:
            history = []
        history.append({
                "role": "user",
                "content": query
        })
        messages = history.copy() # Initialize messages with history
        # List available tools for the LLM
        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            messages=messages,
            tools=available_tools,
            system=SYSTEM_PROMPT
        )
        natural_language_response = []
        for content in response.content:
            if content.type == 'text':
                history.append({
                    "role": "assistant",
                    "content": content.text
                })
                natural_language_response.append(content.text)
                print(f"Claude: {content.text}")
            elif content.type == 'tool_use':
                tool_name = content.name
                tool_args = content.input
                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                print(f"Tool call: {tool_name} with args: {tool_args}")
                print(f"Tool result: {result.content[0].text}")

                # If the tool called was the prompt_user_for_input tool, we need to ask the user for more information.
                if result.content[0].text == "MORE_INFO_NEEDED":
                    # Break to prevent calling LLM unnecessarily
                    break

                # Append the tool call and result to both messages and history
                tool_call = {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "tool_use",
                            "id": content.id,
                            "name": tool_name,
                            "input": tool_args
                        }
                    ]
                }
                tool_result = {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content[0].text
                        }
                    ]
                }

                # Add to messages
                messages.extend([tool_call, tool_result])
                # Add to history
                history.extend([tool_call, tool_result])

                # Get next response from Claude after tool result
                response = self.anthropic.messages.create(
                    model="claude-3-7-sonnet-20250219",
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools,
                    system=SYSTEM_PROMPT
                )
                history.append({
                    "role": "assistant",
                    "content": response.content[0].text
                })
                natural_language_response.append(response.content[0].text)
                print(f"Claude: {response.content[0].text}")
        return_object = {
            "history": history, # History of the chat (needed for tool use flow)
            # Return the final answer by the LLM
            # TODO: Test to see if the last response is always enough
            "LLM_response": natural_language_response[-1], 
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
    print(f"Received request: {req_body}")
    if not isinstance(history, list):
        return jsonify({'error': 'Invalid history format'}), 400
    # Validate history items
    for item in history:
        if not isinstance(item, dict) or 'role' not in item or 'content' not in item:
            return jsonify({'error': 'Invalid history item format'}), 400
        if item['role'] not in ['user', 'assistant']:
            return jsonify({'error': 'Invalid role in history item'}), 400
    try:
        if not query or not isinstance(query, str) or len(query) == 0 or len(query) > 1000:
            return jsonify({'error': 'Invalid query'}), 400
        response = await client.process_query(query, history)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(use_reloader=False, debug=True)

    