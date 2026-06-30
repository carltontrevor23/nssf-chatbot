from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import VECTOR_DB_PATH, LOCAL_EMBEDDING_MODEL
from chatbot.services.scraper import ScrapedPage


@dataclass
class _VectorStoreConfig:
    faiss_index_path: Path
    faiss_pkl_path: Path


class VectorStore:
    """Thin wrapper around LangChain FAISS.

    Expects the FAISS index to exist on disk.
    """

    def __init__(self) -> None:
        base = Path(VECTOR_DB_PATH)
        # Support both shapes used across the repo:
        # - VECTOR_DB_PATH points to a directory containing index.faiss/pkl
        # - VECTOR_DB_PATH points directly to an index.faiss file
        if base.is_dir() or str(base).endswith("faiss_index"):
            self._cfg = _VectorStoreConfig(
                faiss_index_path=base / "index.faiss",
                faiss_pkl_path=base / "index.pkl",
            )
        else:
            # If VECTOR_DB_PATH is index.faiss
            if str(base).endswith(".faiss"):
                self._cfg = _VectorStoreConfig(
                    faiss_index_path=base,
                    faiss_pkl_path=base.with_suffix(".pkl"),
                )
            else:
                self._cfg = _VectorStoreConfig(
                    faiss_index_path=base / "index.faiss",
                    faiss_pkl_path=base / "index.pkl",
                )

    def _load(self):
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings

        if not self._cfg.faiss_index_path.exists() or not self._cfg.faiss_pkl_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found. Expected: {self._cfg.faiss_index_path} and {self._cfg.faiss_pkl_path}"
            )

        embeddings = HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
        return FAISS.load_local(
            str(self._cfg.faiss_index_path.parent),
            embeddings,
            index_name="index",
            allow_dangerous_deserialization=True,
        )

    def get_retriever(self, k: int = 4):
        db = self._load()
        return db.as_retriever(search_kwargs={"k": k})


class NssfVectorStore(VectorStore):
    """Build and load the local FAISS index (used by ingest_data.py)."""

    def build_from_pages(self, pages: list[ScrapedPage]) -> int:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        if not pages:
            raise ValueError("No pages were scraped, so the vector database was not built.")

        documents = [
            Document(
                page_content=page.text,
                metadata={"source": page.url, "title": page.title},
            )
            for page in pages
        ]

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        chunks = splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL)
        vector_store = FAISS.from_documents(chunks, embeddings)
        self._cfg.faiss_index_path.parent.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(self._cfg.faiss_index_path.parent), index_name="index")
        return len(chunks)
