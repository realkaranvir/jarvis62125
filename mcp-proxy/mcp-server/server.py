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
    """Search the internet for information with a given query. Only use if you don't know the answer.
    
    Args:
        query: Search query to look up.
    
    Returns:
        Extracted information from the search results or error message.
    """
    try:
        search_results = None
        search_results = brave_search(query)
        return search_results
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool()
async def execute_command(command: str) -> str:
    """Execute a command in the unix/linux terminal. Ensure to only run commands that won't return super long outputs.
    
    Args:
        command: The command to execute.
    
    Returns:
        The output of the command or an error message.
    """
    try:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return f"Error executing command: {result.stderr.strip()}"
        return result.stdout.strip()
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    mcp.run()