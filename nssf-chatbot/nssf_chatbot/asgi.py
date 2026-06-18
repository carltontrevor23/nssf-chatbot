"""ASGI config for the NSSF chatbot project."""
import os

from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nssf_chatbot.settings")

application = get_asgi_application()
