from typing import Any
from dotenv import load_dotenv
import requests
import subprocess
import os
import sys
import signal
import logging
from datetime import datetime
from pdfminer.high_level import extract_text
from mcp.server.fastmcp import FastMCP
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from functionPrompts import prompts
from LLMs import ollama_llms, claude
import todolist


# Constants
DATA_PATH = "~/jarvis_data"
OBSIDIAN_BASE_PATH = "~/jarvis_data/obsidian_projects"
LOG_FOLDER = "~/jarvis_data/logs"

# Initializing server
mcp = FastMCP()
load_dotenv()
log_dir = os.path.expanduser(LOG_FOLDER)
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "err.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
llm = claude.AnthropicAPI()

todo_list = todolist.TodoList(DATA_PATH, "todolist.txt")

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    print("\nShutting down server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def handleException(e: Exception):
    error = f"An error occurred: {str(e)}"
    logging.error(f"An error occurred: {str(e)}")
    return error

def cleanse_brave_search(response):
    cleansed_result = {}
    i = 0
    if response.get('news'):
        for result in response['news']['results']:
            if result.get('extra_snippets'):
                for snippet in result['extra_snippets']:
                    cleansed_result[f'result_{i}'] = snippet
                    i += 1
            elif result.get('description'):
                cleansed_result[f'result_{i}'] = result['description']
                i += 1
    else:
        cleansed_result = {}
    if response.get('web'):
        for result in response['web']['results']:
            if result.get('extra_snippets'):
                for snippet in result['extra_snippets']:
                    cleansed_result[f'result_{i}'] = snippet
                    i += 1
            elif result.get('description'):
                cleansed_result[f'result_{i}'] = result['description']
                i += 1
    else:
        if len(cleansed_result) == 0:
            return response

    return cleansed_result

def brave_search(query: str, count: int = 20):
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": os.getenv("BRAVE_SEARCH_API_KEY", "")
    }
    params = {
        "q": query,
        "count": count,
        "search_lang": "en",

    }
    response = requests.get(url, headers=headers, params=params)
    clean_response = cleanse_brave_search(response.json())
    return clean_response

@mcp.tool()
async def search_the_internet(query: str) -> str:
    """Search the internet for information with a given query. Only use if you don't know the answer.
    
    Args:
        query: Search query to look up.
    """
    try:
        search_results = None
        search_results = brave_search(query)
        return search_results
    except Exception as e:
        return handleException(e)
    
@mcp.tool()
async def execute_terminal_command(command: str) -> str:
    """Execute a unix command in the unix terminal use ~/ as the root for directories.

    Args:
        command: The unix command to execute in string format.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error executing command: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return handleException(e)
    
@mcp.tool()
async def read_pdf_file_as_txt(file_path: str) -> str:
    """Reads the contents of a PDF file.
    
    Args:
        file_path: The filepath of the pdf file.
    """
    try:
        expanded_file_path = os.path.expanduser(file_path)
        text = extract_text(expanded_file_path)
        return text
    except Exception as e:
        return handleException(e)
    
@mcp.tool()
async def add_to_todo_list(task_name: str):
    """Adds an item to the todo list. Check if an item already exists by calling get_todo_list() first.
    
    Args:
        task_name: The name of the task to add.
    """
    try:
        todo_list.add_task(task_name)
        return f"Task '{task_name}' successfully created"
    except Exception as e:
        return handleException(e)
    
@mcp.tool()
async def remove_from_todo_list(task_name: str):
    """Removes an item from todo list. Check task_name formatting by calling get_todo_list() first.
    
    Args:
        task_name: The name of the task to remove.
    """
    try:
        todo_list.remove_task(task_name)
        return f"Task '{task_name}' successfully removed"
    except Exception as e:
        return handleException(e)
    
@mcp.tool()
async def get_todo_list():
    """Get the todo list"""
    try:
        return "\n".join(todo_list.get_todo_list())
    except Exception as e:
        return handleException(e)

if __name__ == "__main__":
    mcp.run()