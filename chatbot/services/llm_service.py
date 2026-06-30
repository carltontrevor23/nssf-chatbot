from __future__ import annotations

from dataclasses import dataclass
import os

from config import GROQ_API_KEY, GROQ_CHAT_MODEL


@dataclass
class LLMAnswer:
    answer: str


class LLMService:
    """Groq-powered answer generator using LangChain.

    Designed to be compatible with the minimal RAG flow in rag_service.py.
    """

    def __init__(self) -> None:
        # Lazy-load to avoid import issues if optional deps are missing.
        pass

    def generate_answer(
        self,
        question: str,
        context: str,
        chat_history: list[dict[str, str]] | None = None,
    ) -> str:
        from langchain_groq import ChatGroq
        from langchain_core.prompts import ChatPromptTemplate

        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to your environment or .env file."
            )

        llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model=GROQ_CHAT_MODEL,
            temperature=0.2,
        )

        history_text = ""
        if chat_history:
            # Keep it short; server already truncates history.
            last_msgs = chat_history[-6:]
            history_lines = []
            for m in last_msgs:
                role = m.get("role", "user")
                content = (m.get("content") or "").strip()
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are FundBot, answering questions using ONLY the provided context. "
                    "If the context does not contain the answer, say you don't know. "
                    "Be clear and concise. Format lists and headings when helpful.",
                ),
                ("system", "Context:\n{context}"),
                ("system", "Chat history (optional):\n{history_text}"),
                ("human", "Question: {question}"),
            ]
        )

        chain = prompt | llm
        resp = chain.invoke(
            {
                "context": context,
                "question": question,
                "history_text": history_text,
            }
        )

        # LangChain returns AIMessage
        return getattr(resp, "content", str(resp)).strip()

