import json
import os
from pathlib import Path

FIELDS = {'source', 'url', 'start', 'hours', 'zone', 'offset', 'accounts'}

def config_path():
    return Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'VodTimestamps' / 'settings.json'

def load(path=None):
    try:
        data = json.loads((path or config_path()).read_text(encoding='utf-8'))
        return {k: v for k, v in data.items() if k in FIELDS and isinstance(v, str)}
    except (OSError, ValueError, AttributeError):
        return {}

def save(values, path=None):
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps({k: v for k, v in values.items() if k in FIELDS}, indent=2), encoding='utf-8')
    temp.replace(path)
