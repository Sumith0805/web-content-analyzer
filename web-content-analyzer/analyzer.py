"""
analyzer.py
-----------
Core logic for the Web Content Analyzer.

Given a URL (or raw HTML), this module:
  1. Fetches the page (with sane timeouts/error handling).
  2. Parses it with BeautifulSoup.
  3. Extracts metadata (title, meta description, Open Graph tags, language).
  4. Collects all links, splitting internal vs. external.
  5. Extracts headings (h1-h6) to sketch the page outline.
  6. Runs simple regex-based text analysis: word count, reading time estimate,
     and top keyword frequency (stopwords filtered out).
  7. Returns everything as a single structured dict, ready to be serialized
     to JSON or rendered into an HTML report.
"""

from __future__ import annotations

import re
import logging
from collections import Counter
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("analyzer")

DEFAULT_TIMEOUT = 10
DEFAULT_HEADERS = {"User-Agent": "web-content-analyzer/1.0 (+https://github.com/)"}

# A small, common English stopword list -- enough to make keyword frequency
# actually useful without pulling in a heavy NLP dependency.
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "in", "on", "at", "to", "for", "of", "with", "as", "by",
    "that", "this", "it", "its", "from", "we", "you", "your", "our", "they",
    "he", "she", "his", "her", "their", "not", "have", "has", "had", "will",
    "would", "can", "could", "should", "about", "into", "than", "then",
    "so", "if", "up", "out", "no", "yes", "do", "does", "did", "i", "us",
}

WORD_RE = re.compile(r"[A-Za-z']{2,}")


class FetchError(Exception):
    """Raised when the target page can't be retrieved."""


@dataclass
class AnalysisReport:
    url: Optional[str]
    title: Optional[str]
    meta_description: Optional[str]
    language: Optional[str]
    open_graph: Dict[str, str]
    headings: Dict[str, List[str]]
    links_internal: List[str]
    links_external: List[str]
    word_count: int
    estimated_reading_time_minutes: float
    top_keywords: List[Dict[str, int]]

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_html(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Download the page HTML. Raises FetchError on any network/HTTP problem."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.error("Failed to fetch %s: %s", url, exc)
        raise FetchError(f"Could not fetch {url}: {exc}") from exc


def _extract_metadata(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else None

    html_tag = soup.find("html")
    language = html_tag.get("lang") if html_tag else None

    open_graph = {}
    for tag in soup.find_all("meta"):
        prop = tag.get("property", "")
        if prop.startswith("og:") and tag.get("content"):
            open_graph[prop[3:]] = tag["content"].strip()

    return {
        "title": title,
        "meta_description": meta_description,
        "language": language,
        "open_graph": open_graph,
    }


def _extract_headings(soup: BeautifulSoup) -> Dict[str, List[str]]:
    headings: Dict[str, List[str]] = {}
    for level in range(1, 7):
        tag_name = f"h{level}"
        found = [h.get_text(strip=True) for h in soup.find_all(tag_name)]
        if found:
            headings[tag_name] = found
    return headings


def _extract_links(soup: BeautifulSoup, base_url: Optional[str]) -> Dict[str, List[str]]:
    internal, external = [], []
    base_netloc = urlparse(base_url).netloc if base_url else None

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        resolved = urljoin(base_url, href) if base_url else href
        netloc = urlparse(resolved).netloc

        if base_netloc and netloc == base_netloc:
            internal.append(resolved)
        elif netloc:
            external.append(resolved)
        else:
            internal.append(resolved)

    # De-duplicate while preserving order.
    return {
        "internal": list(dict.fromkeys(internal)),
        "external": list(dict.fromkeys(external)),
    }


def _analyze_text(soup: BeautifulSoup, top_n: int = 15) -> Dict:
    # Strip script/style before extracting visible text.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    words = [w.lower() for w in WORD_RE.findall(text)]
    word_count = len(words)

    filtered = [w for w in words if w not in STOPWORDS]
    counts = Counter(filtered)
    top_keywords = [{"word": w, "count": c} for w, c in counts.most_common(top_n)]

    # Average adult reading speed ~200 words/minute.
    reading_time = round(word_count / 200, 1) if word_count else 0.0

    return {
        "word_count": word_count,
        "estimated_reading_time_minutes": reading_time,
        "top_keywords": top_keywords,
    }


def analyze_html(html: str, url: Optional[str] = None) -> AnalysisReport:
    """Analyze raw HTML (already fetched) and return a structured report."""
    soup = BeautifulSoup(html, "html.parser")

    metadata = _extract_metadata(soup)
    headings = _extract_headings(soup)
    links = _extract_links(soup, url)
    text_stats = _analyze_text(soup)

    return AnalysisReport(
        url=url,
        title=metadata["title"],
        meta_description=metadata["meta_description"],
        language=metadata["language"],
        open_graph=metadata["open_graph"],
        headings=headings,
        links_internal=links["internal"],
        links_external=links["external"],
        word_count=text_stats["word_count"],
        estimated_reading_time_minutes=text_stats["estimated_reading_time_minutes"],
        top_keywords=text_stats["top_keywords"],
    )


def analyze_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> AnalysisReport:
    """Fetch a URL and analyze it in one step."""
    html = fetch_html(url, timeout=timeout)
    return analyze_html(html, url=url)
