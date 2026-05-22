import logging
import tempfile
from pathlib import Path

import reddit_crawler.storage as storage_mod
from .article import extract_article, is_external_url
from .crawler import crawl
from .schema import normalize_reddit_post
from .storage import save

logger = logging.getLogger(__name__)


def handler(event: dict, context) -> dict:
    """AWS Lambda entry point."""
    storage_mod.DATA_DIR = Path(tempfile.gettempdir()) / "reddit-crawler-data"

    data = crawl()
    items: list[dict] = []
    for subreddit_data in data["subreddits"]:
        subreddit = subreddit_data["name"]
        for post in subreddit_data["posts"]:
            url = post.get("url", "")
            article = extract_article(url) if is_external_url(url) else None
            items.append(normalize_reddit_post(post, subreddit, article))

    filepath = save(items, data["crawled_at"])
    logger.info("Lambda crawl complete — %d posts saved to %s", len(items), filepath)

    return {"statusCode": 200, "body": f"Saved {len(items)} posts to {filepath}"}
