from typing import Any
from dotenv import load_dotenv
import requests
import os
import sys
import signal
from mcp.server.fastmcp import FastMCP

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

def brave_search(query: str, count: int = 4):
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
    return response.json()

@mcp.tool()
async def search_the_internet(query: str, search_engine: int) -> str:
    """Search the internet for information with a given query. Only use if you don't already have the information.
    
    Args:
        query: Search query to look up.
        search_engine: 0 for Brave Search. More to be added later.
    
    Returns:
        Extracted information from the search results or error message.
    """
    try:
        search_results = None
        if search_engine == 0:
            search_results = brave_search(query)
        else:
            return "Unsupported search engine. Please use Brave Search (0) for now."
        return search_results
    except Exception as e:
        return f"An error occurred: {str(e)}"

@mcp.tool()
async def execute_command_on_macos_terminal(command: str) -> str:
    """Execute a command on the macOS terminal.
    
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