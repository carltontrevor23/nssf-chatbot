from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
LOCAL_EMBEDDING_MODEL = os.getenv(
    "LOCAL_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
VECTOR_DB_PATH = Path(os.getenv("VECTOR_DB_PATH", "vector_db/faiss_index"))
if not VECTOR_DB_PATH.is_absolute():
    VECTOR_DB_PATH = BASE_DIR / VECTOR_DB_PATH

NSSF_BASE_URL = os.getenv("NSSF_BASE_URL", "https://www.nssfug.org/")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
