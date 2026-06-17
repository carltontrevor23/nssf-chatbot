"""LLM integration layer for generating chatbot responses."""
from __future__ import annotations

from django.conf import settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq


class LlmServiceError(Exception):
    """Raised when the language model cannot produce a response."""


class GroqLlmService:
    """Small wrapper around Groq chat models."""

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise LlmServiceError("GROQ_API_KEY is not configured.")

        self.chat_model = ChatGroq(
            model=settings.GROQ_CHAT_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.2,
        )

    def generate_answer(
        self,
        question: str,
        context: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate a concise support response grounded in retrieved context."""
        history_text = self._format_recent_history(chat_history or [])
        system_prompt = (
            "You are a helpful website support assistant for NSSF Uganda. "
            "Answer using only the provided NSSF website context and the recent "
            "conversation. Be concise, practical, and friendly. If the context "
            "does not contain the answer, say you do not have enough information "
            "from the NSSF website and suggest contacting NSSF directly. Do not "
            "invent fees, dates, legal requirements, or eligibility rules."
        )
        user_prompt = f"""
NSSF website context:
{context}

Recent conversation:
{history_text}

User question:
{question}
"""

        try:
            response = self.chat_model.invoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            )
        except Exception as exc:
            raise LlmServiceError("The AI service is currently unavailable.") from exc

        return str(response.content).strip()

    def _format_recent_history(self, chat_history: list[dict[str, str]]) -> str:
        if not chat_history:
            return "No previous messages in this session."

        recent_messages = chat_history[-6:]
        lines = []
        for message in recent_messages:
            role = message.get("role", "user").title()
            content = message.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
