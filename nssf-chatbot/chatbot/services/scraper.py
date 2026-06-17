"""Website scraping utilities for collecting public NSSF Uganda content."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class ScrapedPage:
    """Simple container for page content collected from the website."""

    url: str
    title: str
    text: str


class NssfWebsiteScraper:
    """Crawl selected pages from the public NSSF Uganda website."""

    def __init__(self, base_url: str, max_pages: int = 40, timeout: int = 15):
        self.base_url = base_url.rstrip("/") + "/"
        self.max_pages = max_pages
        self.timeout = timeout
        self.base_domain = urlparse(self.base_url).netloc
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "NSSFChatbotIndexer/1.0 "
                    "(educational support assistant; respects public pages)"
                )
            }
        )

    def crawl(self, seed_paths: Iterable[str] | None = None) -> list[ScrapedPage]:
        """Crawl the website and return pages with meaningful text."""
        queue = self._build_seed_urls(seed_paths)
        visited: set[str] = set()
        pages: list[ScrapedPage] = []

        while queue and len(pages) < self.max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue

            visited.add(current_url)
            html = self._download_html(current_url)
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            text = self._extract_text(soup)
            title = self._extract_title(soup)

            if len(text) > 200:
                pages.append(ScrapedPage(url=current_url, title=title, text=text))

            for link in self._extract_links(soup, current_url):
                if link not in visited and link not in queue:
                    queue.append(link)

        return pages

    def _build_seed_urls(self, seed_paths: Iterable[str] | None) -> list[str]:
        if not seed_paths:
            return [self.base_url]

        return [self._normalize_url(urljoin(self.base_url, path)) for path in seed_paths]

    def _download_html(self, url: str) -> str | None:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException:
            return None

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None

        return response.text

    def _extract_title(self, soup: BeautifulSoup) -> str:
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        heading = soup.find(["h1", "h2"])
        return heading.get_text(" ", strip=True) if heading else "NSSF Uganda"

    def _extract_text(self, soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "noscript", "svg", "form", "footer"]):
            tag.decompose()

        main_content = soup.find("main") or soup.find("article") or soup.body or soup
        lines = [
            line.strip()
            for line in main_content.get_text("\n", strip=True).splitlines()
            if line.strip()
        ]
        return "\n".join(lines)

    def _extract_links(self, soup: BeautifulSoup, page_url: str) -> list[str]:
        links: list[str] = []
        for anchor in soup.find_all("a", href=True):
            absolute_url = self._normalize_url(urljoin(page_url, anchor["href"]))
            if self._is_allowed_url(absolute_url):
                links.append(absolute_url)
        return links

    def _is_allowed_url(self, url: str) -> bool:
        parsed_url = urlparse(url)
        if parsed_url.netloc != self.base_domain:
            return False
        if parsed_url.scheme not in {"http", "https"}:
            return False
        blocked_extensions = (".jpg", ".jpeg", ".png", ".gif", ".pdf", ".zip", ".docx")
        return not parsed_url.path.lower().endswith(blocked_extensions)

    def _normalize_url(self, url: str) -> str:
        clean_url, _fragment = urldefrag(url)
        return clean_url.rstrip("/") + "/"
