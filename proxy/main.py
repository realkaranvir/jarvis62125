from quart import Quart, request, jsonify
from quart_cors import cors

import httpx

app = Quart(__name__)
app = cors(app, allow_origin="*") # TODO: change later

@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/proxy/audio-query', methods=['POST'])
async def audio_query():
    """
    Audio query endpoint. Takes in an audio blob, gets transcription from STT server, 
    gets the MCP server's response, and returns audio blob and MCP JSON response.
    """
    files = await request.files
    speech_to_text_url = "http://localhost:5001/transcribe"

    async with httpx.AsyncClient() as client:
        speech_to_text_response = await client.post(speech_to_text_url, files=files)

    data = speech_to_text_response.json()
    transcription = data.get('transcription')
    
    if not transcription:
        return jsonify({'error': 'transcription is null'}), 500
    elif len(transcription) == 0:
        return jsonify({'error': 'transcription is empty'}), 500

if __name__ == "__main__":
    app.run(use_reloader=False, debug=True, port=5002) # TODO: change