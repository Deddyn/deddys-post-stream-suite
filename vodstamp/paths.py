"""Paths relative to the portable application, never to a developer profile."""
import sys
from pathlib import Path

ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
TOOLS = ROOT / 'tools'
