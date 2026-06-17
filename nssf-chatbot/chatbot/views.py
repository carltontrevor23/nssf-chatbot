"""Views for rendering the chat UI and serving chat responses."""
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .services.rag_service import RagService, RagServiceError


logger = logging.getLogger(__name__)


@require_GET
def chat_page(request):
    """Display the chatbot interface."""
    request.session.setdefault("chat_history", [])
    return render(request, "chatbot/chat.html")


@require_POST
def chat_api(request):
    """Receive a user message and return an AI-generated response as JSON."""
    user_message = request.POST.get("message", "").strip()

    if not user_message:
        return JsonResponse({"error": "Please enter a message."}, status=400)

    if len(user_message) > 1000:
        return JsonResponse(
            {"error": "Please keep your message under 1000 characters."},
            status=400,
        )

    chat_history = request.session.get("chat_history", [])

    try:
        rag_service = RagService()
        bot_response = rag_service.answer_question(user_message, chat_history)
    except RagServiceError as exc:
        logger.warning("Chatbot service error: %s", exc)
        return JsonResponse({"error": str(exc)}, status=503)
    except Exception:
        logger.exception("Unexpected chatbot error")
        return JsonResponse(
            {"error": "Sorry, something went wrong while preparing a response."},
            status=500,
        )

    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": bot_response})
    request.session["chat_history"] = chat_history[-20:]
    request.session.modified = True

    return JsonResponse({"response": bot_response})
