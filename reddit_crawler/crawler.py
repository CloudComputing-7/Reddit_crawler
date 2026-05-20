import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from . import config

logger = logging.getLogger(__name__)

STATE_FILE = Path("state.json")
MAX_SEEN_IDS = 500
REDDIT_BASE_URL = "https://www.reddit.com"
REQUEST_DELAY = 2  # 서브레딧 간 대기 (초)


def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"seen_post_ids": []}


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def fetch_posts(subreddit_name: str, seen_ids: set) -> list[dict]:
    url = f"{REDDIT_BASE_URL}/r/{subreddit_name}/new.json"
    headers = {"User-Agent": config.REDDIT_USER_AGENT}
    params = {"limit": config.POSTS_PER_SUBREDDIT}

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            posts = []
            for child in data["data"]["children"]:
                post = child["data"]
                if post["id"] in seen_ids:
                    continue
                posts.append({
                    "id": post["id"],
                    "title": post["title"],
                    "url": post["url"],
                    "score": post["score"],
                    "num_comments": post["num_comments"],
                    "created_utc": datetime.fromtimestamp(
                        post["created_utc"], tz=timezone.utc
                    ).isoformat(),
                    "selftext": post.get("selftext", ""),
                })
            return posts

        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            wait = (2 ** attempt) * 5 if status == 429 else 2 ** attempt
            logger.warning(
                "HTTP %d for r/%s (attempt %d/3), retrying in %ds",
                status, subreddit_name, attempt + 1, wait,
            )
            if attempt < 2:
                time.sleep(wait)
        except requests.RequestException as e:
            logger.warning("Request error for r/%s: %s (attempt %d/3)", subreddit_name, e, attempt + 1)
            if attempt < 2:
                time.sleep(2 ** attempt)

    logger.error("Failed to fetch r/%s after 3 attempts", subreddit_name)
    return []


def crawl() -> dict:
    state = _load_state()
    seen_ids = set(state.get("seen_post_ids", []))

    crawled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    result: dict = {"crawled_at": crawled_at, "subreddits": []}
    new_ids: list[str] = []

    for i, subreddit_name in enumerate(config.SUBREDDITS):
        if i > 0:
            time.sleep(REQUEST_DELAY)
        posts = fetch_posts(subreddit_name, seen_ids)
        new_ids.extend(p["id"] for p in posts)
        result["subreddits"].append({"name": subreddit_name, "posts": posts})
        logger.info("Fetched %d new posts from r/%s", len(posts), subreddit_name)

    all_ids = list(seen_ids) + new_ids
    state["seen_post_ids"] = all_ids[-MAX_SEEN_IDS:]
    state["last_crawled_at"] = crawled_at
    _save_state(state)

    return result
