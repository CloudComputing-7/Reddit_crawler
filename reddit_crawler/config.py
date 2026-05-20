import os

from dotenv import load_dotenv

load_dotenv()

REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "reddit-crawler/1.0")

SUBREDDITS: list[str] = os.getenv("SUBREDDITS", "cybersecurity,netsec,Malware").split(",")
POSTS_PER_SUBREDDIT: int = int(os.getenv("POSTS_PER_SUBREDDIT", "25"))
CRAWL_INTERVAL_HOURS: int = int(os.getenv("CRAWL_INTERVAL_HOURS", "1"))
