from pathlib import Path
import os

from dotenv import load_dotenv

# Shared runtime configuration for the chatbot services.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
LOCAL_EMBEDDING_MODEL = os.getenv(
    "LOCAL_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
VECTOR_DB_PATH = BASE_DIR / os.getenv("VECTOR_DB_PATH", "vector_db/faiss_index")
NSSF_BASE_URL = os.getenv("NSSF_BASE_URL", "https://www.nssfug.org/")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
