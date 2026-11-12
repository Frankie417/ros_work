"""Locate this standalone homework tree; importing does not open devices."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SDK_DIR = ROOT / 'sdk' / 'arm5dof_python_uservo'

def configure_sdk():
    if not (SDK_DIR / 'arm5dof_uservo.py').is_file():
        raise FileNotFoundError(str(SDK_DIR))
    if str(SDK_DIR) not in sys.path:
        sys.path.insert(0, str(SDK_DIR))
    return SDK_DIR
