from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "nssf-chatbot"))

from app import app  # noqa: E402,F401
