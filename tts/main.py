import wave
from piper import PiperVoice
from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse
import io

app = FastAPI()

voice = PiperVoice.load("./models/jarvis/jarvis-high.onnx", use_cuda=False)
    
@app.post("/generate-speech")
def generate_speech(
    text: str = Form(...)
):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        voice.synthesize_wav(text, wav_file)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=output.wav"}
    )