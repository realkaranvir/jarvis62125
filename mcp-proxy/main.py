import sys
import signal
import asyncio
from dotenv import load_dotenv
from quart import Quart, request, jsonify
from quart_cors import cors
from LLMs import ollama_llms, claude
from mcp_flow import MCPClient

load_dotenv() # Load environment variables from .env

client = MCPClient(ollama_llms.OllamaAPI("jarvis5-qwen:latest"))

app = Quart(__name__)
app = cors(app, allow_origin="*") # TODO: Change to certain origins later

@app.before_serving
async def startup():
    """Start the server connection before serving requests"""
    try:
        await client.connect_to_server("mcp-server/server.py")
    except Exception as e:
        print(f"Error connecting to server: {str(e)}")
        sys.exit(1)

@app.after_serving
async def shutdown():
    """Clean up resources after serving requests"""
    print("Shutting down server gracefully...")
    await client.cleanup()

# Register signal handler to handle SIGINT (Ctrl+C)
def signal_handler(sig, frame):
    """Handle SIGINT gracefully."""
    asyncio.create_task(shutdown())  # Schedule the shutdown task

signal.signal(signal.SIGINT, signal_handler)

@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/query', methods=['POST'])
async def query_llm():
    """Endpoint to query the LLM"""
    req_body = await request.get_json()
    query = req_body.get('query')
    history = req_body.get('history', [])

    if not isinstance(history, list):
        return jsonify({'error': 'Invalid history format'}), 400
    # Validate history items
    for item in history:
        if not isinstance(item, dict) or 'role' not in item or 'content' not in item:
            return jsonify({'error': 'Invalid history item format'}), 400
        if item['role'] not in ['user', 'assistant', 'system']:
            return jsonify({'error': 'Invalid role in history item'}), 400
    try:
        if not query or not isinstance(query, str) or len(query) == 0 or len(query) > 1000:
            return jsonify({'error': 'Invalid query'}), 400
        response = await client.process_query(query, history)
        return jsonify({'response': response}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(use_reloader=False, debug=True) # TODO: change