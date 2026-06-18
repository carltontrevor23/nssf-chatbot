"""Build the local FAISS vector database from public NSSF Uganda pages.

Run this script whenever the NSSF website content changes:

    python ingest_data.py
"""
import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nssf_chatbot.settings")
django.setup()

from django.conf import settings  # noqa: E402

from chatbot.services.scraper import NssfWebsiteScraper  # noqa: E402
from chatbot.services.vector_store import NssfVectorStore  # noqa: E402


SEED_PATHS = [
    "/",
    "/about-us/",
    "/membership/",
    "/employers/",
    "/benefits/",
    "/savings-products/",
    "/contact-us/",
]


def main():
    """Crawl NSSF pages and rebuild the vector database."""
    print("Starting NSSF Uganda content ingestion...")
    scraper = NssfWebsiteScraper(
        base_url=settings.NSSF_BASE_URL,
        max_pages=int(os.getenv("NSSF_MAX_PAGES", "50")),
    )
    pages = scraper.crawl(seed_paths=SEED_PATHS)
    print(f"Scraped {len(pages)} pages.")

    vector_store = NssfVectorStore()
    chunk_count = vector_store.build_from_pages(pages)
    print(f"Saved {chunk_count} content chunks to {settings.VECTOR_DB_PATH}.")


if __name__ == "__main__":
    main()
