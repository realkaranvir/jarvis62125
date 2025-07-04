from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import utils

class MCPClient:
    def __init__(self, llm):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack() # Handles closing of async resources
        self.llm = llm
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
        """Process a query"""

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