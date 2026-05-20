import os
import sys

import pytest


def reload_config(env_vars: dict = {}):
    for key, val in env_vars.items():
        os.environ[key] = val
    if "reddit_crawler.config" in sys.modules:
        del sys.modules["reddit_crawler.config"]
    import reddit_crawler.config as cfg
    return cfg


def test_default_subreddits():
    os.environ.pop("SUBREDDITS", None)
    if "reddit_crawler.config" in sys.modules:
        del sys.modules["reddit_crawler.config"]
    import reddit_crawler.config as cfg
    assert cfg.SUBREDDITS == ["cybersecurity", "netsec", "Malware"]


def test_custom_subreddits():
    cfg = reload_config({"SUBREDDITS": "Python,golang"})
    assert cfg.SUBREDDITS == ["Python", "golang"]


def test_posts_per_subreddit_default():
    os.environ.pop("POSTS_PER_SUBREDDIT", None)
    if "reddit_crawler.config" in sys.modules:
        del sys.modules["reddit_crawler.config"]
    import reddit_crawler.config as cfg
    assert cfg.POSTS_PER_SUBREDDIT == 25


def test_crawl_interval_default():
    os.environ.pop("CRAWL_INTERVAL_HOURS", None)
    if "reddit_crawler.config" in sys.modules:
        del sys.modules["reddit_crawler.config"]
    import reddit_crawler.config as cfg
    assert cfg.CRAWL_INTERVAL_HOURS == 1


def test_user_agent_default():
    os.environ.pop("REDDIT_USER_AGENT", None)
    if "reddit_crawler.config" in sys.modules:
        del sys.modules["reddit_crawler.config"]
    import reddit_crawler.config as cfg
    assert "reddit-crawler" in cfg.REDDIT_USER_AGENT
