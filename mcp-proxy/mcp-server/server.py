from typing import Any
import requests
from mcp.server.fastmcp import FastMCP
import sys
import signal

# Initializing server
mcp = FastMCP()

# Constants
CURRENT_TEMP = 53

# Handle SIGINT (Ctrl+C) gracefully
def signal_handler(sig, frame):
    print("\nShutting down server gracefully...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Test Function
def get_current_temperature() -> str:
    return f"Current Temperature: {CURRENT_TEMP}"

@mcp.tool()
async def get_temperature(city: str) -> str:
    """Get the current temperature at a given city in California.
    
    Args:
        city: Full name of a city in California. Required.
    
    """

    # Get the weather
    temp = get_current_temperature()
    return f"{city}: {temp} degrees"

@mcp.tool()
async def send_notification(notification: str) -> str:
    """Send a notification to the phone.
    
    Args:
        notification: The notification message to send. Required.
    
    """
    # Simulate sending a notification
    print(f"Notification sent: {notification}")
    return "Notification sent successfully!"

if __name__ == "__main__":
    # Initialize and run the server
    print("Intializing server...")
    mcp.run()


