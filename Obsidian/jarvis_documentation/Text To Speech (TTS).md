#### Runs via Piper
- [Github](https://github.com/rhasspy/piper)
- Can use any `.onnx` file for the voice model
#### Installation
```
cd tts
source .venv/bin/activate
cd piper/src/python_run
pip install -e .
pip install -r requirements_http.txt
pip install piper-phonemize-cross
```
#### Running
```
cd tts/models
python -m piper.http_server --model jarvis/jarvis-high.onnx
```