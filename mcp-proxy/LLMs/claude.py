from anthropic import Anthropic

class AnthropicAPI:
    def __init__(self):
        self.anthropic = Anthropic()
        self.context_len = 128000
        self.response_limit = self.context_len // 20
        self.NAME = "Jarvis"
        self.SYSTEM_PROMPT = f"Your name is {self.NAME}. You are a formal, concise assistant who always refers to the user as sir. You answer in no more than two sentences. Do not ask follow-up questions unless absolutely necessary to understand the current query. Do not offer additional information, suggestions, or clarifications unless directly requested. You are helpful but reserved. If a question cannot be answered without more information, state that clearly and wait for further input. You have access to tools, but you will only use them when the question cannot be answered directly."

    def query_llm(self, messages: list, tools: list):
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
            system=self.SYSTEM_PROMPT
        )
        print(response)
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
    
    def query_helper(self, query):
        messages=[{
            "role": "user",
            "content": query
        }]
        response = self.anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            messages=messages,
            system=self.SYSTEM_PROMPT
        )
        return response