#### Runs via Piper
- [Github](https://github.com/rhasspy/piper)
- Can use any `.onnx` file for the voice model
#### Installation
```
cd tts
uv python install 3.10
uv run python3.10 -m venv .venv
source .venv/bin/activate
cd piper/src/python_run
pip install -e .
pip install -r requirements_http.txt
pip install piper-phonemize-cross
cd ../../.. (go back to tts dir)
mkdir models (place models here)
```
[Jarvis](https://huggingface.co/jgkawell/jarvis/tree/main/en/en_GB/jarvis/high)
#### Running
```
cd tts
source .venv/bin/activate
python -m piper.http_server --model models/jarvis/jarvis-high.onnx
```