from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import httpx, base64, json, re

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TODO: tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
async def transcribe_file(audio_file: UploadFile) -> str:
    stt_url = "http://stt:5001/transcribe"
    files = {"file": (audio_file.filename, await audio_file.read(), audio_file.content_type)}

    async with httpx.AsyncClient() as client:
        resp = await client.post(stt_url, files=files)

    transcription = resp.json().get("transcription")
    if not transcription:
        raise HTTPException(status_code=500, detail="STT error: transcription empty")
    return transcription


async def query_mcp_server(query: str, session_id: str):
    mcp_url = "http://agent:5003/query"
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(mcp_url, data={"query": query, "session_id": session_id})
    return resp.json()

async def text_to_speech(text: str) -> str:
    if not text:
        raise HTTPException(status_code=500, detail="TTS error: text empty")

    tts_url = f"http://tts:5008/generate-speech"
    async with httpx.AsyncClient(timeout=120.0) as client:
        wav_resp = await client.post(tts_url, data={"text": text})

    return base64.b64encode(wav_resp.content).decode("utf-8")

# Endpoints
@app.get("/proxy/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/proxy/audio-query")
async def audio_query(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    use_tts: str = Form("false")
):

    # Core pipeline
    transcription = await transcribe_file(file)
    mcp_resp = await query_mcp_server(transcription, session_id)

    if use_tts.lower() != "true":
        return JSONResponse(content=mcp_resp)

    text = mcp_resp.get("response", {}).get("LLM_response", "")
    new_text = re.sub(r"karan", "Kah-run", text, flags=re.IGNORECASE) # TODO: implement in agent
    try:
        wav_b64 = await text_to_speech(new_text)
        mcp_resp.setdefault("response", {})["tts_wav"] = wav_b64
    except Exception:
        # Fail soft—return MCP response even if TTS fails
        pass

    return JSONResponse(content=mcp_resp)

@app.post("/proxy/text-query")
async def text_query(
    query: str = Form(...),
    session_id: str = Form(...)
):
    data = await query_mcp_server(query, session_id)
    return JSONResponse(content=data)