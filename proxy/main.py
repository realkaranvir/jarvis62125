from quart import Quart, request, jsonify
from quart_cors import cors

import base64

from urllib.parse import quote

import json
import httpx

app = Quart(__name__)
app = cors(app, allow_origin="*") # TODO: change later

async def transcribe_file(audio_file):
    speech_to_text_url = "http://localhost:5001/transcribe"

    files = {
        "file": (audio_file.filename, audio_file.stream, audio_file.content_type)
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(speech_to_text_url, files=files)

    data = response.json()
    transcription = data.get("transcription")
    
    if not transcription:
        raise Exception("STT error: Transcription is Null")
    elif len(transcription) == 0:
        raise Exception("STT error: Transcription is empty")
    
    return transcription
    
async def query_mcp_server(query: str, history: list):
    mcp_url = "http://127.0.0.1:5000/query"

    payload = {
        "query": query,
        "history": history
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(mcp_url, json=payload)

    data = response.json()
    return data

async def text_to_speech(text: str):
    if not text:
        raise Exception("TTS error: text is empty")
    
    encoded_text = quote(text)
    text_to_speech_url = f"http://localhost:5008/?text={encoded_text}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        wav = await client.get(text_to_speech_url)

    wav_bytes = wav.content

    encoded_wav = base64.b64encode(wav_bytes).decode("utf-8")

    return encoded_wav

@app.route("/proxy/health", methods=["GET"])
async def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route("/proxy/audio-query", methods=["POST"])
async def audio_query():
    """
    Audio query endpoint. Takes in an audio blob and history, gets transcription from STT server, 
    gets the MCP server's response, and returns audio blob and MCP JSON response.
    """
    files = await request.files
    form = await request.form

    audio_file = files.get("file")
    history_str = form.get("history")

    use_tts = False
    if form.get("use_tts").lower() == "true":
        use_tts = True

    if not audio_file or not history_str:
        return jsonify({"error": "Missing audio file or history"}), 400

    try:
        history = json.loads(history_str)
        if not isinstance(history, list):
            raise ValueError("History is not an array")
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in history"}), 400

    mcp_response = None
    try:
        transcription = await transcribe_file(audio_file)
        mcp_response = await query_mcp_server(transcription, history)
        print(mcp_response)
        if not use_tts:
            return jsonify(mcp_response), 200
    except Exception as e:
        return jsonify({"error": e}), 500
    
    try:
        wav = await text_to_speech(mcp_response.get("response").get("LLM_response"))
        full_response = mcp_response
        full_response.get("response")["tts_wav"] = wav
        return jsonify(full_response), 200
    except Exception as e:
        return jsonify({"error": e}), 500

@app.route("/proxy/text-query", methods=["POST"])
async def text_query():
    """
    Text query endpoint. Takes in query and history, forwards request to mcp server, and returns the result.
    """
    form = await request.form

    query = form.get("query")
    history_str = form.get("history")

    if not history_str:
        return jsonify({"error": "Missing history"}), 400

    try:
        history = json.loads(history_str)
        if not isinstance(history, list):
            raise ValueError("History is not an array")
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in history"}), 400    

    try:
        data = await query_mcp_server(query, history)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": e}), 500

if __name__ == "__main__":
    app.run(use_reloader=False, debug=True, port=5002) # TODO: change