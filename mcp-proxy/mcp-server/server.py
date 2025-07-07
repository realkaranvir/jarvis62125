from typing import Any
from dotenv import load_dotenv
import requests
import os
import sys
import signal

from mcp.server.fastmcp import FastMCP

# Constants
response_cap = 500 # in characters

# Initializing server
mcp = FastMCP()
load_dotenv()

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    print("\nShutting down server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
browser = None
tab = None

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
    """Search the internet for information with a given query. Only use if you don't know the answer
    
    Args:
        query: Search query to look up
    
    Returns:
        Extracted information from the search results or error message
    """
    try:
        search_results = None
        search_results = brave_search(query)
        return search_results
    except Exception as e:
        return f"An error occurred: {str(e)}"
    
@mcp.tool()
async def list_obsidian_projects() -> str:
    """Lists the obsidian projects under ~/jarvis_data/obsidian_projects

    Args:

    Returns:
        List of Obsidian projects or error message
    """
    base_path = os.path.expanduser("~/jarvis_data/obsidian_projects")

    if not os.path.exists(base_path):
        return "Error: Obsidian project directory doesn't exist."

    projects = [
        name for name in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, name)) and name[0] != "."
    ]

    if not projects:
        return "No Obsidian projects found."
    else:
        return "\n".join(projects)

@mcp.tool()
async def create_obsidian_project(project_name: str) -> str:
    """Creates a new Obsidian project folder under ~/jarvis_data/obsidian_projects. Make sure to check if the project already exists first by calling list_obsidian_projects().
    
    Args:
        project_name: Name of the project folder. Format the user's input into snake_case when passing in.

    Returns:
        The result of the operation (success or failure)
    """
    base_path = os.path.expanduser("~/jarvis_data/obsidian_projects")
    vault_path = os.path.join(base_path, project_name)

    try:
        os.makedirs(vault_path, exist_ok=False)
        return f"Created new Obsidian vault: {vault_path}"
    except FileExistsError:
        return f"Project '{project_name}' already exists."

@mcp.tool()
async def create_new_file_in_obsidian_project(project_name:str, file_name: str):
    """Creates a new file within the given Obsidian project. Make sure to check if the project already exists and its name by first calling list_obsidian_projects().
    
    Args:
        project_name: Name of the project folder.
        file_name: Name of the new file to create. Ask the user for the filename beforehand and format using Title Case.

    Returns:
        The result of the operation (success or failure)
    """
    base_path = os.path.expanduser("~/jarvis_data/obsidian_projects")
    vault_path = os.path.join(base_path, project_name)
    file_path = os.path.join(vault_path, file_name)

    try:
        with open(file_path, "x") as file:
            pass  # No content written, just create the file
        return f"File '{file_path}' was created successfully."
    except FileExistsError:
        return f"Error: File '{file_path}' already exists."
    except PermissionError:
        return f"Error: Permission denied when trying to create '{file_path}'."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    mcp.run()