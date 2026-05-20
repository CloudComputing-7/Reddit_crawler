import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from . import config
from .article import extract_article, is_external_url
from .crawler import crawl
from .storage import save

logger = logging.getLogger(__name__)


def run_crawl() -> None:
    logger.info("Crawl started")
    data = crawl()

    for subreddit_data in data["subreddits"]:
        for post in subreddit_data["posts"]:
            url = post.get("url", "")
            if is_external_url(url):
                logger.debug("Extracting article: %s", url)
                post["article"] = extract_article(url)

    filepath = save(data)
    total = sum(len(s["posts"]) for s in data["subreddits"])
    logger.info("Crawl complete — %d posts saved to %s", total, filepath)


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
