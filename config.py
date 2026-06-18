from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_CHAT_MODEL = os.environ.get("GROQ_CHAT_MODEL", "groq-1o-mini")
VECTOR_DB_PATH = os.environ.get("VECTOR_DB_PATH", str(BASE_DIR / "vector_db" / "faiss_index" / "index.faiss"))
LOCAL_EMBEDDING_MODEL = os.environ.get("LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "5"))
