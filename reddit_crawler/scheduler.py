import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from . import config
from .article import extract_article, is_external_url
from .crawler import crawl
from .schema import normalize_reddit_post
from .storage import save

logger = logging.getLogger(__name__)


def run_crawl() -> None:
    logger.info("Crawl started")
    data = crawl()

    items: list[dict] = []
    for subreddit_data in data["subreddits"]:
        subreddit = subreddit_data["name"]
        for post in subreddit_data["posts"]:
            url = post.get("url", "")
            article = None
            if is_external_url(url):
                logger.debug("Extracting article: %s", url)
                article = extract_article(url)
            items.append(normalize_reddit_post(post, subreddit, article))

    filepath = save(items, data["crawled_at"])
    logger.info("Crawl complete — %d posts saved to %s", len(items), filepath)


def start() -> None:
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_crawl,
        "interval",
        hours=config.CRAWL_INTERVAL_HOURS,
        next_run_time=datetime.now(),
    )
    logger.info(
        "Scheduler started. Crawling every %d hour(s). Press Ctrl+C to stop.",
        config.CRAWL_INTERVAL_HOURS,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
