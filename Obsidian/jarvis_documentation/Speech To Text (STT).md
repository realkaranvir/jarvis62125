#### Runs via Speaches
- [Github](https://github.com/speaches-ai/speaches)
- Needs to be converted to just faster-whisper
#### Installation
```
cd speaches
uv venv
source .venv/bin/activate
uv sync --all-extras
```
#### Running
```
source .venv/bin/activate
export ALLOW_ORIGINS='["*"]'
uvicorn --factory --host 0.0.0.0 speaches.main:create_app
```
