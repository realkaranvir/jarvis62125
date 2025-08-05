from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import torch

app = FastAPI()

# Allow all origins for now — update in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup model config
device_type = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device_type == "cuda" else "float32"
default_model_size = "tiny" if device_type == "cuda" else "tiny"

print("Initializing WhisperModel:")
print(f"Device Type: {device_type}")
print(f"Compute Type: {compute_type}")
print(f"Model Size: {default_model_size}")

model = WhisperModel(default_model_size, device=device_type, compute_type=compute_type)

# Utility functions
def transcribe_wav_file(wav_file):
    segments, info = model.transcribe(
        wav_file.file, 
        beam_size=5, 
        vad_filter=True, 
        language="en", 
        vad_parameters={"threshold": 0.6, "neg_threshold": 0.3}
    )
    print(f"Detected language '{info.language}' with probability {info.language_probability}")
    return segments

def process_segments(segments: list):
    text_elements = (segment.text for segment in segments)
    return " ".join(text_elements)

# Routes
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        segments = transcribe_wav_file(file)
        transcription = process_segments(segments)
        return {"transcription": transcription}
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))