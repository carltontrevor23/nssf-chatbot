FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY nssf-chatbot/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY nssf-chatbot/ .

# Expose port 7860 (required for HF Spaces)
EXPOSE 7860

# Set Django settings
ENV DJANGO_SETTINGS_MODULE=nssf_chatbot.settings

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:7860"]
