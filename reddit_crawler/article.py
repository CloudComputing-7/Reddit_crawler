import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import trafilatura
from newspaper import Article as NewspaperArticle

logger = logging.getLogger(__name__)

SKIP_DOMAINS = {
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
    "redd.it",
    "i.redd.it",
    "v.redd.it",
}


def is_external_url(url: str) -> bool:
    if not url:
        return False
    try:
        domain = urlparse(url).netloc.lower()
        return bool(domain) and domain not in SKIP_DOMAINS
    except Exception:
        return False


def extract_article(url: str) -> dict | None:
    # 1차: trafilatura
    try:
        downloaded = trafilatura.fetch_url(url, timeout=10)
        if downloaded:
            result = trafilatura.bare_extraction(
                downloaded,
                include_comments=False,
                include_tables=False,
            )
            if result and result.get("text"):
                return {
                    "title": result.get("title") or "",
                    "content": result["text"],
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                }
    except Exception as e:
        logger.debug("trafilatura failed for %s: %s", url, e)

    # 2차 fallback: newspaper3k
    try:
        article = NewspaperArticle(url)
        article.download()
        article.parse()
        if article.text:
            return {
                "title": article.title or "",
                "content": article.text,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
            }
    except Exception as e:
        logger.debug("newspaper3k failed for %s: %s", url, e)

    return None
