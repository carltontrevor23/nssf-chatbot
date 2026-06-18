"""FAISS vector database helpers for NSSF website content."""
from __future__ import annotations

from pathlib import Path

from config import LOCAL_EMBEDDING_MODEL, RAG_TOP_K, VECTOR_DB_PATH
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .scraper import ScrapedPage


class VectorStoreError(Exception):
    """Raised when the FAISS index cannot be loaded or created."""


class NssfVectorStore:
    """Build and query the local FAISS index."""

    def __init__(self, index_path: Path | None = None):
        self.index_path = Path(index_path or VECTOR_DB_PATH)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=LOCAL_EMBEDDING_MODEL,
        )

    def build_from_pages(self, pages: list[ScrapedPage]) -> int:
        """Create a FAISS index from scraped pages and return chunk count."""
        if not pages:
            raise VectorStoreError("No pages were scraped, so the vector database was not built.")

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

        vector_store = FAISS.from_documents(chunks, self.embeddings)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(self.index_path))
        return len(chunks)

    def load(self) -> FAISS:
        """Load the FAISS index from disk."""
        if not self.index_path.exists():
            raise VectorStoreError(
                "The vector database was not found. Run `python ingest_data.py` first."
            )

        return FAISS.load_local(
            str(self.index_path),
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

    def retrieve(self, question: str, top_k: int | None = None) -> list[Document]:
        """Return the most relevant NSSF content chunks for a question."""
        vector_store = self.load()
        return vector_store.similarity_search(question, k=top_k or RAG_TOP_K)
