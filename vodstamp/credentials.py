from pathlib import Path

def load_riot_key(path=None):
    path = path or Path(__file__).resolve().parent.parent / 'Riot API.txt'
    try:
        key = path.read_text(encoding='utf-8-sig').strip()
    except (OSError, UnicodeError):
        raise ValueError('Impossibile leggere Riot API.txt nella cartella dell’app. Usa un file UTF-8 contenente soltanto la chiave.') from None
    if not key or any(c.isspace() for c in key):
        raise ValueError('Riot API.txt deve contenere soltanto la chiave Riot, su una riga.')
    return key
