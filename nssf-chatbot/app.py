from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chatbot.services.rag_service import RagService, RagServiceError

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NSSF Uganda Chatbot")
app.state.chat_sessions = {}

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "chatbot" / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "chatbot" / "templates" / "chatbot")


def _get_session_id(session_id: str | None) -> str:
    return session_id or str(uuid.uuid4())


def _get_chat_history(session_id: str) -> list[dict[str, str]]:
    return app.state.chat_sessions.setdefault(session_id, [])


@app.get("/")
async def chat_page(request: Request, session_id: str | None = Cookie(default=None)):
    session_id = _get_session_id(session_id)
    _get_chat_history(session_id)
    response = templates.TemplateResponse(
        request,
        "chat_fastapi.html",
        {"request": request},
    )
    if not request.cookies.get("session_id"):
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return response


@app.post("/chat", name="chat_api")
async def chat_api(
    request: Request,
    message: str = Form(...),
    session_id: str | None = Cookie(default=None),
) -> JSONResponse:
    message_text = message.strip()
    if not message_text:
        return JSONResponse({"error": "Please enter a message."}, status_code=400)

    if len(message_text) > 1000:
        return JSONResponse(
            {"error": "Please keep your message under 1000 characters."},
            status_code=400,
        )

    session_id = _get_session_id(session_id)
    chat_history = _get_chat_history(session_id)

    try:
        rag_service = RagService()
        bot_response = rag_service.answer_question(message_text, chat_history)
    except RagServiceError as exc:
        logger.warning("Chatbot service error: %s", exc)
        return JSONResponse({"error": str(exc)}, status_code=503)
    except Exception:
        logger.exception("Unexpected chatbot error")
        return JSONResponse(
            {"error": "Sorry, something went wrong while preparing a response."},
            status_code=500,
        )

    chat_history.append({"role": "user", "content": message_text})
    chat_history.append({"role": "assistant", "content": bot_response})
    app.state.chat_sessions[session_id] = chat_history[-20:]

    response = JSONResponse({"response": bot_response})
    if not request.cookies.get("session_id"):
        response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return response
