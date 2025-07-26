def get_task_from_query_prompt(query, choices):
    choicesList = "\n".join(choices)
    return f'''You are a classifier whose job is to identify if a query refers to an existing task in the todo list.
First, extract the task name mentioned in the query (if any).
Here are the available tasks:
{choicesList}

Given the following query: “{query}”, figure out which existing task (if any) it refers to, even if the wording or formatting is slightly different.
If it matches one of the tasks, your response should be exactly the matching task name from the list above. 
If it does not match any, your response should be None. If no task is mentioned in the query, your response should be None.'''

def get_query_type_prompt(query):
    return f'''You are a classifier whose job is to determine the type of action requested on a todo list. 
The possible actions are:
- add: Adding a new task to the todo list.
- delete: Removing a task from the todo list.
- list: Listing all tasks currently on the todo list.
- none: the user query relates to none of the above operations.

Given the following query: “{query}”, determine whether it is an add, delete, or list action. 
Your response should be one of the following words only: add, delete, list, or none.'''

def generate_task_name_from_query(query):
    return f'''You are an extractor who extracts the task name from a query.
For example, if the query is "add cutting my nails to my todo list", your response would be "cut my nails".
RETURN ONLY THE TASK NAME, NOT THE WHOLE QUERY.

Given the following query: “{query}”, extract out just the task name. Your response should just be the task name.'''