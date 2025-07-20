import ollama
import utils

class OllamaAPI:
    def __init__(self):
        self.model = 'jarvis5-qwen:latest'
        self.context_len = 40000
        self.response_limit = self.context_len // 100
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

    def query_llm(self, messages: list, tools: list):
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
                    'type': tool.inputSchema.get('type', ''),
                    'required': tool.inputSchema.get('required', []),
                    'properties': tool.inputSchema.get('properties', '')
                }
            }
        } for tool in tools]

        if (len(messages) > 10):
            messages = messages[len(messages) - 10:]

        response = ollama.chat(model=self.model,think=False, messages=messages, tools=available_tools)
        tool_calls = []
        llm_response = ""
        if response.message.tool_calls:
            tool_calls = [{'name': tool.function.name, 'args': tool.function.arguments, 'tool_use_id': str(self.tool_use_id_counter) } for tool in response.message.tool_calls]
        # Sometimes model returns tool call in content message
        if response.message.content and response.message.content[:13] == 'type=tool_use':
            info = utils.parse_tool_string(response.message.content)
            tool_calls.append({'name': info['name'], 'args': info['input'], 'tool_use_id': info['id']})
        else:
            llm_response = response.message.content
        result = {'llm_response': llm_response, 'tool_calls': tool_calls}
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