from faster_whisper import WhisperModel
from quart import Quart, request, jsonify
from quart_cors import cors
import torch

app = Quart(__name__)
app = cors(app, allow_origin="*") # TODO: change later

device_type = "cuda" if (torch.cuda.is_available()) else "cpu"
compute_type = "float16" if (device_type == "cuda") else "float32"
default_model_size = "tiny" if (device_type == "cuda") else "tiny"

print("Initializing TTS:")
print(f"Device Type: {device_type}")
print(f"Compute Type: {compute_type}")
print(f"Model Size: {default_model_size}")

model = WhisperModel(default_model_size, device=device_type, compute_type=compute_type)

def load_model(model_size):
    # Run on GPU with FP16
    model = WhisperModel(model_size, device=device_type, compute_type=compute_type)

def transcribe_wav_file(wav_file):
    segments, info = model.transcribe(wav_file, beam_size=5, vad_filter=True, language="en", vad_parameters={"threshold": 0.6, "neg_threshold": 0.3})
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    return segments

def process_segments(segments: list):
    text_elements = (segment.text for segment in segments)
    transcription = " ".join(text_elements)
    return transcription

@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/transcribe', methods=['POST'])
async def transcribe():
    """Endpoint to transcribe audio files"""
    files = await request.files
    if 'file' not in files:
        return jsonify({'error': "No file part in the request"}), 400
    file = (await request.files)['file']
    try:
        transcription = process_segments(transcribe_wav_file(file))
        return jsonify({'transcription': transcription}), 200
    except Exception as e:
        print(f'Unexpected error: {e}')
        return jsonify({'error': str(e)}), 400
    
if __name__ == "__main__":
    app.run(use_reloader=False, debug=True, port=5001) # TODO: change