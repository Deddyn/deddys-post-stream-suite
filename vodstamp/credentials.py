from pathlib import Path
from .paths import ROOT

def load_riot_key(path=None):
    path = path or ROOT / 'Riot API.txt'
    try:
        key = path.read_text(encoding='utf-8-sig').strip()
    except (OSError, UnicodeError):
        raise ValueError('Create Riot API.txt next to the app, containing only your Riot key (UTF-8). Click the Riot Personal API Key link to apply.') from None
    if not key or any(c.isspace() for c in key):
        raise ValueError('Riot API.txt must contain only your Riot key on one line.')
    return key
