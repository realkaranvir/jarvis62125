### STT

#### Installation
cd speaches
uv venv
source .venv/bin/activate
uv sync --all-extras

#### Running
export ALLOW_ORIGINS='["*"]'
uvicorn --factory --host 0.0.0.0 speaches.main:create_app

### TTS

#### Installation
source .venv/bin/activate
cd tts/piper/src/python_run
pip install -e .
pip install -r requirements_http.txt
pip install piper-phonemize-cross

#### Running
cd tts/models
python -m piper.http_server --model jarvis/jarvis-high.onnx

### MCP

#### Installation
cd mcp-proxy/mcp-server
source .venv/bin/activate
uv sync
deactivate

cd mcp-proxy
source .venv/bin/activate
uv sync

#### Running
cd mcp-proxy
python main.py

### Frontend

#### Installation
npm install

#### Running
npm run dev