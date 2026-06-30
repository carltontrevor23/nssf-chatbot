from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from config import RAG_TOP_K

logger = logging.getLogger(__name__)


class RagServiceError(RuntimeError):
    pass


@dataclass
class RagResult:
    answer: str
    sources: list[dict[str, Any]]


class RagService:
    """Minimal RAG service implementation.

    The repository you have currently only contains the FastAPI/Django entry
    points and static assets. This class provides a working implementation
    compatible with:
      - nssf-chatbot/nssf-chatbot/app.py

    It attempts to use the project's local FAISS vector DB if available.
    If the vector DB isn't built yet, it raises RagServiceError.
    """

    def __init__(self) -> None:
        # Lazy imports so the module can be imported even when optional deps
        # aren't fully initialized yet.
        self._vector_store = None
        self._llm = None

    def _load_vector_store(self):
        if self._vector_store is not None:
            return self._vector_store

        try:
            from chatbot.services.vector_store import VectorStore
        except Exception as exc:
            raise RagServiceError(f"Vector store module missing: {exc}") from exc

        self._vector_store = VectorStore()
        return self._vector_store

    def _load_llm(self):
        if self._llm is not None:
            return self._llm

        try:
            from chatbot.services.llm_service import LLMService
        except Exception as exc:
            raise RagServiceError(f"LLM service module missing: {exc}") from exc

        self._llm = LLMService()
        return self._llm

    def answer_question(self, question: str, chat_history: list[dict[str, str]]) -> str:
        question = (question or "").strip()
        if not question:
            raise RagServiceError("Empty question")

        vector_store = self._load_vector_store()
        retriever = vector_store.get_retriever(k=RAG_TOP_K)

        docs = retriever.get_relevant_documents(question)
        if not docs:
            raise RagServiceError("I couldn't find relevant information in the knowledge base.")

        llm = self._load_llm()
        # Keep the protocol simple: llm_service produces final answer from
        # question + retrieved context.
        context = "\n\n".join(getattr(d, "page_content", str(d)) for d in docs)
        return llm.generate_answer(question=question, context=context, chat_history=chat_history)

