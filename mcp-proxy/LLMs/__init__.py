# All files in /LLMs/ dir need to adhere to this abstract class:

# response_limit: int
# context_len: int

# def query_llm(self, messages: list, tools: list, system_prompt: str): 
    # returns:
        #    {
        #        "llm_response": "<string>", 
        #        "tool_calls": [
        #            {
        #            "name": "<tool_function_name>",
        #            "args": "<tool_function_arguments>",
        #            "tool_use_id": "<unique_tool_use_id>"
        #            },
        #            {
        #            "name": "<tool_function_name_2>",
        #            "args": "<tool_function_arguments_2>",
        #            "tool_use_id": "<unique_tool_use_id_2>"
        #            }
        #        ]
        #    }

# def format_tool_call(self, tool_use_id, tool_name, tool_args):
    # returns:
        #    {
        #        "role": "assistant",
        #        "content": [
        #            {
        #                "type": "tool_use",
        #                "id": <tool_use_id>,
        #                "name": <tool_name>,
        #                "input": <tool_args>
        #            }
        #        ]
        #    }

# def format_tool_result(self, tool_use_id, result):
    # returns:
        #    {
        #        "role": "user",
        #        "content": [
        #            {
        #                "type": "tool_result",
        #                "id": <tool_use_id>,
        #                "content": <result>
        #            }
        #        ]
        #    }
