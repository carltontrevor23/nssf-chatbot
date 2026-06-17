"""WSGI config for the NSSF chatbot project."""
import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nssf_chatbot.settings")

application = get_wsgi_application()
