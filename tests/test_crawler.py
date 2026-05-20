import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from reddit_crawler.crawler import (
    _load_state,
    _save_state,
    crawl,
    fetch_posts,
)


def make_response(posts: list[dict], status_code: int = 200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = {
        "data": {
            "children": [{"data": p} for p in posts]
        }
    }
    mock_resp.raise_for_status = MagicMock()
    if status_code >= 400:
        http_err = requests.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = http_err
    return mock_resp


def make_post(id_="a1", title="Title", url="https://example.com", score=10, num_comments=3, selftext=""):
    return {
        "id": id_,
        "title": title,
        "url": url,
        "score": score,
        "num_comments": num_comments,
        "created_utc": 1716206400.0,
        "selftext": selftext,
    }


# --- state 파일 테스트 ---

def test_load_state_returns_empty_when_no_file(tmp_path, monkeypatch):
    import reddit_crawler.crawler as crawl_mod
    monkeypatch.setattr(crawl_mod, "STATE_FILE", tmp_path / "state.json")
    assert _load_state() == {"seen_post_ids": []}


def test_save_and_load_state_roundtrip(tmp_path, monkeypatch):
    import reddit_crawler.crawler as crawl_mod
    monkeypatch.setattr(crawl_mod, "STATE_FILE", tmp_path / "state.json")
    _save_state({"seen_post_ids": ["id1", "id2"]})
    assert _load_state()["seen_post_ids"] == ["id1", "id2"]


# --- fetch_posts 테스트 ---

def test_fetch_posts_returns_normalized_posts():
    post = make_post("a1", "Title A", "https://example.com")
    with patch("reddit_crawler.crawler.requests.get", return_value=make_response([post])):
        posts = fetch_posts("cybersecurity", seen_ids=set())

    assert len(posts) == 1
    assert posts[0]["id"] == "a1"
    assert posts[0]["title"] == "Title A"
    assert "created_utc" in posts[0]


def test_fetch_posts_skips_seen_ids():
    posts_data = [
        make_post("seen1", "Old", "https://example.com"),
        make_post("new1", "New", "https://example.com/new"),
    ]
    with patch("reddit_crawler.crawler.requests.get", return_value=make_response(posts_data)):
        posts = fetch_posts("cybersecurity", seen_ids={"seen1"})

    assert len(posts) == 1
    assert posts[0]["id"] == "new1"


def test_fetch_posts_retries_on_429():
    post = make_post()
    responses = [
        make_response([], status_code=429),
        make_response([], status_code=429),
        make_response([post]),
    ]
    with patch("reddit_crawler.crawler.requests.get", side_effect=responses), \
         patch("reddit_crawler.crawler.time.sleep"):
        posts = fetch_posts("cybersecurity", seen_ids=set())

    assert len(posts) == 1


def test_fetch_posts_returns_empty_after_3_failures():
    err_resp = make_response([], status_code=503)
    with patch("reddit_crawler.crawler.requests.get", return_value=err_resp), \
         patch("reddit_crawler.crawler.time.sleep"):
        posts = fetch_posts("cybersecurity", seen_ids=set())

    assert posts == []


# --- crawl() 통합 테스트 ---

def test_crawl_updates_seen_ids(tmp_path, monkeypatch):
    import reddit_crawler.crawler as crawl_mod
    monkeypatch.setattr(crawl_mod, "STATE_FILE", tmp_path / "state.json")

    post = make_post("newid")
    with patch("reddit_crawler.crawler.requests.get", return_value=make_response([post])), \
         patch("reddit_crawler.crawler.config.SUBREDDITS", ["cybersecurity"]), \
         patch("reddit_crawler.crawler.time.sleep"):
        crawl()

    state = _load_state()
    assert "newid" in state["seen_post_ids"]


def test_crawl_result_structure(tmp_path, monkeypatch):
    import reddit_crawler.crawler as crawl_mod
    monkeypatch.setattr(crawl_mod, "STATE_FILE", tmp_path / "state.json")

    post = make_post("id1")
    with patch("reddit_crawler.crawler.requests.get", return_value=make_response([post])), \
         patch("reddit_crawler.crawler.config.SUBREDDITS", ["cybersecurity"]), \
         patch("reddit_crawler.crawler.time.sleep"):
        result = crawl()

    assert "crawled_at" in result
    assert len(result["subreddits"]) == 1
    assert result["subreddits"][0]["name"] == "cybersecurity"
    assert result["subreddits"][0]["posts"][0]["id"] == "id1"
