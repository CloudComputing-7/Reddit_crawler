import logging
import tempfile
from pathlib import Path

import reddit_crawler.storage as storage_mod
from .article import extract_article, is_external_url
from .crawler import crawl
from .storage import save

logger = logging.getLogger(__name__)


def handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point.
    /tmp/reddit-crawler-data/ 에 저장. 추후 S3 저장으로 교체 예정.
    """
    storage_mod.DATA_DIR = Path(tempfile.gettempdir()) / "reddit-crawler-data"

    data = crawl()
    for subreddit_data in data["subreddits"]:
        for post in subreddit_data["posts"]:
            url = post.get("url", "")
            if is_external_url(url):
                post["article"] = extract_article(url)

    filepath = save(data)
    total = sum(len(s["posts"]) for s in data["subreddits"])
    logger.info("Lambda crawl complete — %d posts saved to %s", total, filepath)

    return {"statusCode": 200, "body": f"Saved {total} posts to {filepath}"}
