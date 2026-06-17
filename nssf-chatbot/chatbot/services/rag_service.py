"""High-level Retrieval-Augmented Generation service."""
from __future__ import annotations

from .llm_service import GroqLlmService, LlmServiceError
from .vector_store import NssfVectorStore, VectorStoreError


class RagServiceError(Exception):
    """Raised when the chatbot cannot complete a RAG response."""


class RagService:
    """Retrieve NSSF context and ask the LLM for a grounded answer."""

    def __init__(self):
        try:
            self.vector_store = NssfVectorStore()
            self.llm_service = GroqLlmService()
        except (LlmServiceError, VectorStoreError) as exc:
            raise RagServiceError(str(exc)) from exc

    def answer_question(self, question: str, chat_history: list[dict[str, str]]) -> str:
        """Answer a user question using RAG."""
        try:
            documents = self.vector_store.retrieve(question)
        except VectorStoreError as exc:
            raise RagServiceError(str(exc)) from exc

        context = self._format_context(documents)
        try:
            return self.llm_service.generate_answer(question, context, chat_history)
        except LlmServiceError as exc:
            raise RagServiceError(str(exc)) from exc

    def _format_context(self, documents) -> str:
        if not documents:
            return "No matching NSSF website content was found."

        context_blocks = []
        for index, document in enumerate(documents, start=1):
            source = document.metadata.get("source", "Unknown source")
            title = document.metadata.get("title", "NSSF Uganda")
            context_blocks.append(
                f"[Source {index}: {title} - {source}]\n{document.page_content}"
            )
        return "\n\n".join(context_blocks)
