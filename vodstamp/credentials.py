"""Read and write the portable Riot API credential file."""

import os
import tempfile
from pathlib import Path

from .paths import ROOT

KEY_LABEL = "Paste your API Key here:"
INSTRUCTIONS_MARKER = "--- Instructions ---"
KEY_TEMPLATE = f"""{KEY_LABEL}



{INSTRUCTIONS_MARKER}
1. Open the Riot Developer Portal and sign in: https://developer.riotgames.com/
2. Select Register Product, then choose the Personal application type: https://developer.riotgames.com/app-type
3. Enter any product name, choose League of Legends, paste the description below, and submit it for approval.
4. Once approved, go to Apps, open the registered project, and copy its Personal API Key.
5. Paste the key above or into the masked field in the app, then click Test Riot.

Application description:
I use this desktop tool privately to match my EUW League of Legends games to my livestream VODs, create timestamps, and trim recordings of my own games.

Riot Developer Portal documentation: https://developer.riotgames.com/docs/portal
"""


def _path(path):
    return Path(path) if path is not None else ROOT / "Riot API.txt"


def _validate_key(key):
    key = str(key).strip()
    if not key or any(character.isspace() for character in key):
        raise ValueError("Enter one Riot API key without spaces or extra lines.")
    return key


def _key_from_text(text):
    before_marker = text.split(INSTRUCTIONS_MARKER, 1)[0]
    lines = before_marker.splitlines()
    label_index = next((i for i, line in enumerate(lines) if line.strip().startswith(KEY_LABEL)), None)
    if label_index is None:
        candidates = [line.strip() for line in lines if line.strip()]
    else:
        label_line = lines[label_index].strip()
        same_line = label_line[len(KEY_LABEL):].strip()
        candidates = ([same_line] if same_line else []) + [line.strip() for line in lines[label_index + 1:] if line.strip()]
    if len(candidates) != 1:
        raise ValueError("Riot API.txt does not contain one valid Riot API key.")
    return _validate_key(candidates[0])


def ensure_riot_key_file(path=None):
    """Create the instructional credential file if it does not already exist."""
    target = _path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as file:
            file.write(KEY_TEMPLATE)
    except FileExistsError:
        pass
    return target


def load_riot_key(path=None):
    target = _path(path)
    if not target.exists():
        try:
            ensure_riot_key_file(target)
        except (OSError, UnicodeError):
            raise ValueError("Could not create Riot API.txt next to the app.") from None
    try:
        text = target.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        raise ValueError("Could not read Riot API.txt. Check that it is a UTF-8 text file.") from None
    return _key_from_text(text)


def save_riot_key(key, path=None):
    """Atomically save a key while retaining an existing instruction section."""
    key = _validate_key(key)
    target = _path(path)
    instructions = KEY_TEMPLATE.split(INSTRUCTIONS_MARKER, 1)[1]
    try:
        if target.exists():
            existing = target.read_text(encoding="utf-8-sig")
            if INSTRUCTIONS_MARKER in existing:
                instructions = existing.split(INSTRUCTIONS_MARKER, 1)[1]
        content = f"{KEY_LABEL}\n{key}\n\n\n\n{INSTRUCTIONS_MARKER}{instructions}"
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as file:
                file.write(content)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_name, target)
        except BaseException:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass
            raise
    except (OSError, UnicodeError):
        raise OSError("Could not save Riot API.txt. Check that the folder is writable.") from None
    return target
