# FundBot

A production-ready starter chatbot for the NSSF Uganda website. It uses Django for the web application and a Retrieval-Augmented Generation (RAG) pipeline so answers are grounded in content scraped from public NSSF Uganda pages.

## Overall Architecture

The project is intentionally split into small, beginner-friendly layers:

- `chatbot/views.py` handles HTTP requests, CSRF-protected form posts, session chat history, validation, and JSON responses.
- `chatbot/services/scraper.py` crawls selected public pages from `https://www.nssfug.org/` and extracts useful text.
- `chatbot/services/vector_store.py` splits scraped content, creates local Hugging Face embeddings, and stores them in a local FAISS vector database.
- `chatbot/services/llm_service.py` sends the retrieved context and user question to the configured Groq chat model.
- `chatbot/services/rag_service.py` coordinates retrieval and answer generation.
- `ingest_data.py` rebuilds the vector database whenever website content changes.

## Why These Packages Were Chosen

- **Django 5**: stable Python web framework with built-in sessions, CSRF protection, templates, routing, and admin tooling.
- **SQLite**: simple default database for local development.
- **Bootstrap 5**: fast responsive styling without a heavy frontend framework.
- **LangChain**: provides document objects, text splitting, vector store integration, and model wrappers.
- **FAISS**: fast local vector search for development and small-to-medium knowledge bases.
- **Local Hugging Face Embeddings**: converts NSSF content and user questions into vectors for semantic search without an embeddings API bill.
- **Groq Chat Model**: generates conversational responses using retrieved NSSF context.
- **python-dotenv**: loads local environment variables without hard-coding secrets.
- **requests + BeautifulSoup**: simple, readable website crawling and text extraction.

## How The RAG Pipeline Works

1. `ingest_data.py` crawls selected NSSF Uganda website pages.
2. The scraper extracts page titles, URLs, and readable text.
3. The vector store splits long pages into smaller overlapping chunks.
4. Local embeddings are generated for each chunk.
5. Chunks and embeddings are saved in `vector_db/faiss_index`.
6. When a visitor asks a question, the app embeds the question and retrieves the most relevant chunks.
7. The Groq chat model receives the retrieved context, recent session history, and the user's question.
8. The answer is returned to the browser as JSON and displayed in the chat interface.

## Data Flow Through The Application

Browser -> `POST /chat/` -> Django view -> `RagService` -> FAISS retrieval -> Groq chat model -> JSON response -> Bootstrap chat UI.

The user's conversation history is stored in the Django session for the current browser session. API keys stay server-side in environment variables.

## Project Structure

```text
nssf-chatbot/
├── chatbot/
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── rag_service.py
│   │   ├── scraper.py
│   │   └── vector_store.py
│   ├── static/
│   ├── templates/
│   │   └── chatbot/
│   │       └── chat.html
│   ├── urls.py
│   └── views.py
├── nssf_chatbot/
│   ├── settings.py
│   └── urls.py
├── vector_db/
├── ingest_data.py
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

Run these commands from the project root.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set:

```text
GROQ_API_KEY=your_real_groq_api_key
GROQ_CHAT_MODEL=llama-3.1-8b-instant
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SECRET_KEY=a_long_random_secret_key
DEBUG=True
```

## Run Migrations

```powershell
python manage.py migrate
```

## Build The Vector Database

```powershell
python ingest_data.py
```

This command crawls public NSSF Uganda pages, chunks the text, generates embeddings, and stores the FAISS index in `vector_db/faiss_index`.

## Start The Development Server

```powershell
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## API Endpoint

`GET /`

Displays the chat interface.

`POST /chat/`

Receives a message and returns JSON.

Example request:

```json
{
  "message": "How do I register for NSSF?"
}
```

Example response:

```json
{
  "response": "To register for NSSF..."
}
```

## Security Notes

- CSRF protection is enabled through Django middleware and the template form token.
- API keys are loaded from environment variables and are never exposed to the browser.
- User input is validated for empty messages and excessive length.
- Server errors are logged but not exposed to users.
- In production, set `DEBUG=False`, use a strong `SECRET_KEY`, and configure `ALLOWED_HOSTS`.

## Future PostgreSQL Setup

For production, replace SQLite with PostgreSQL:

1. Install `psycopg[binary]`.
2. Add database environment variables such as `DATABASE_URL`.
3. Update `DATABASES` in `nssf_chatbot/settings.py` or use `dj-database-url`.
4. Run `python manage.py migrate`.

The FAISS vector database can remain on disk for a small deployment, but larger deployments should consider a managed vector database such as pgvector, Pinecone, Weaviate, or Qdrant.

## Deployment Checklist

- Set `DEBUG=False`.
- Set a strong `SECRET_KEY`.
- Configure `ALLOWED_HOSTS`.
- Use HTTPS.
- Run `python manage.py collectstatic`.
- Use a production server such as Gunicorn or uWSGI behind Nginx.
- Store `.env` values in your hosting provider's secret manager.
- Schedule `python ingest_data.py` to refresh the knowledge base when NSSF website content changes.
