import json
import os
from pathlib import Path

APP_DIR = Path(os.environ.get("APPDATA", Path.home())) / "JarvisVoiceStudio"
SETTINGS_FILE = APP_DIR / "settings.json"
HISTORY_FILE = APP_DIR / "history.json"
AUDIO_DIR = APP_DIR / "audio"
DEFAULTS = {"provider":"local", "voice":"JARVIS — Official Voice · Faber (pt-BR)", "locale":"pt-BR",
            "speed":1.0, "volume":0.85, "model":"gpt-4o-mini-tts", "cloud_voice":"onyx",
            "expressiveness":0.35, "local_voice":""}

def read_settings():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    try: return {**DEFAULTS, **json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))}
    except (OSError, ValueError): return dict(DEFAULTS)

def write_settings(data):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps({k:v for k,v in data.items() if k != "api_key"}, indent=2, ensure_ascii=False), encoding="utf-8")
