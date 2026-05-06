from __future__ import annotations

import re
from collections import deque
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


def normalize_url(raw_url: str) -> str:
    value = raw_url.strip()
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    if not parsed.netloc:
        raise ValueError("Invalid URL")
    return value


def fetch_source_summary(domain_url: str) -> str:
    """Fetch lightweight page context for better interview questions."""
    try:
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            response = client.get(domain_url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        description = meta.get("content", "").strip() if meta else ""
        body_text = " ".join(soup.get_text(" ", strip=True).split())[:400]
        summary = " | ".join(part for part in [title, description, body_text] if part)
        return summary[:600] if summary else "No clear page content extracted."
    except Exception:
        return "Could not fetch page content; user-provided context will be used."


def summarize_text_source(text: str) -> str:
    cleaned = " ".join(text.split())
    return cleaned[:800] if cleaned else "No text provided."


def fetch_domain_scan_summary(domain_url: str, max_pages: int = 6) -> str:
    """Scan same-domain pages and produce concise context summary."""
    try:
        start = normalize_url(domain_url)
        parsed_start = urlparse(start)
        base_domain = parsed_start.netloc
        queue = deque([start])
        visited: set[str] = set()
        snippets: list[str] = []

        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            while queue and len(visited) < max_pages:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                try:
                    response = client.get(current)
                    response.raise_for_status()
                except Exception:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                title = (soup.title.string or "").strip() if soup.title else ""
                meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
                description = meta.get("content", "").strip() if meta else ""
                body = " ".join(soup.get_text(" ", strip=True).split())[:260]
                part = " | ".join(piece for piece in [title, description, body] if piece)
                if part:
                    snippets.append(part[:320])

                for anchor in soup.find_all("a", href=True):
                    href = anchor.get("href", "").strip()
                    if not href or href.startswith("#"):
                        continue
                    absolute = urljoin(current, href)
                    parsed = urlparse(absolute)
                    if parsed.scheme not in {"http", "https"}:
                        continue
                    if parsed.netloc != base_domain:
                        continue
                    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
                    if normalized and normalized not in visited:
                        queue.append(normalized)

        if not snippets:
            return "Could not extract enough domain context from the provided link."
        combined = " || ".join(snippets[:max_pages])
        return combined[:1800]
    except Exception:
        return "Could not extract enough domain context from the provided link."
