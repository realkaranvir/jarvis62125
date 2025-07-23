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
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    print("\nShutting down server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def handleException(e: Exception):
    error = f"An error occurred: {str(e)}"
    logging.debug(f"An error occurred: {str(e)}")
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

def safe_join(base_dir: str, user_input_path: str) -> str:
    """
    Safely join base_dir with user_input_path to prevent directory traversal.
    
    Returns the absolute safe path if valid, or raises a ValueError if invalid.
    """
    # Expand ~ to home directory
    base_dir = os.path.expanduser(base_dir)
    user_input_path = os.path.expanduser(user_input_path)

    # Join and normalize
    full_path = os.path.abspath(os.path.join(base_dir, user_input_path))

    # Normalize base_dir after expansion
    base_dir = os.path.abspath(base_dir)
    if not full_path.startswith(base_dir + os.sep):
        raise ValueError("Invalid path: attempting to access outside of base directory.")

    return full_path


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
        return handleException(e)
    
@mcp.tool()
async def execute_terminal_command(command: str) -> str:
    """Execute a unix command in the unix terminal use ~/ as the root for directories.

    Args:
        command: The unix command to execute in string format.
    
    Returns:
        The output of the command or an error message.
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
    """Reads the contents of a PDF file
    
    Args:
        file_path: The filepath of the pdf file.

    Returns:
        The contents of the PDF file
    """
    try:
        expanded_file_path = os.path.expanduser(file_path)
        text = extract_text(expanded_file_path)
        return text
    except Exception as e:
        return handleException(e)

if __name__ == "__main__":
    mcp.run()