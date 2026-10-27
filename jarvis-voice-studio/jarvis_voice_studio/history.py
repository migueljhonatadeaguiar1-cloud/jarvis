import json
import uuid
from datetime import datetime
from .settings import APP_DIR, HISTORY_FILE

def all_items():
    try: return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError): return []

def add(text, path, duration, provider, name=None):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    items = all_items(); items.insert(0, {"id":uuid.uuid4().hex, "name":name or datetime.now().strftime("JARVIS_%Y%m%d_%H%M%S.wav"),
        "date":datetime.now().astimezone().isoformat(timespec="minutes"), "duration":duration,
        "text":text, "path":str(path), "provider":provider})
    HISTORY_FILE.write_text(json.dumps(items[:100], ensure_ascii=False, indent=2), encoding="utf-8")
    return items[0]

def save(items): HISTORY_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
