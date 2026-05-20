# Reddit Crawler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** r/cybersecurity, r/netsec, r/Malware 서브레딧의 최신 게시물을 1시간마다 수집해 JSON으로 저장하는 Python 크롤러를 구현한다. 뉴스 링크가 포함된 게시물은 기사 본문도 함께 저장한다.

**Architecture:** `reddit_crawler/` 패키지 안에 config, crawler, article, storage, scheduler 모듈을 분리한다. 로컬 진입점은 `main.py`, Lambda stub은 `reddit_crawler/lambda_handler.py`. APScheduler BlockingScheduler가 매 1시간마다 크롤링을 트리거한다.

**Tech Stack:** Python 3.11+, praw 7.7+, trafilatura 1.6+, newspaper3k 0.2+, apscheduler 3.10+, python-dotenv 1.0+, pytest 7+, pytest-mock

---

## File Map

| 파일 | 역할 |
|------|------|
| `requirements.txt` | 의존성 선언 |
| `.env.example` | API 키 템플릿 |
| `.gitignore` | data/, logs/, .env 제외 |
| `main.py` | 로컬 진입점, 로깅 설정 |
| `reddit_crawler/__init__.py` | 빈 패키지 마커 |
| `reddit_crawler/config.py` | 환경변수 로드 및 상수 노출 |
| `reddit_crawler/crawler.py` | PRAW로 Reddit 게시물 수집, state.json 관리 |
| `reddit_crawler/article.py` | 외부 URL 판별, trafilatura/newspaper3k로 본문 추출 |
| `reddit_crawler/storage.py` | data/ 디렉토리에 JSON 파일 저장 |
| `reddit_crawler/scheduler.py` | APScheduler 실행 루프 |
| `reddit_crawler/lambda_handler.py` | Lambda entry point stub |
| `tests/__init__.py` | 빈 패키지 마커 |
| `tests/test_config.py` | config 단위 테스트 |
| `tests/test_storage.py` | storage 단위 테스트 |
| `tests/test_article.py` | article 단위 테스트 |
| `tests/test_crawler.py` | crawler 단위 테스트 |

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `reddit_crawler/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: 디렉토리 생성**

```bash
mkdir -p reddit_crawler tests data logs
```

- [ ] **Step 2: requirements.txt 작성**

```
praw>=7.7
trafilatura>=1.6
newspaper3k>=0.2
apscheduler>=3.10
python-dotenv>=1.0
requests>=2.31
pytest>=7.0
pytest-mock>=3.12
```

- [ ] **Step 3: .env.example 작성**

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=reddit-crawler/1.0 by u/yourusername

SUBREDDITS=cybersecurity,netsec,Malware
POSTS_PER_SUBREDDIT=25
CRAWL_INTERVAL_HOURS=1
```

- [ ] **Step 4: .gitignore 작성**

```
.env
data/
logs/
state.json
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
build/
.DS_Store
```

- [ ] **Step 5: 빈 __init__.py 생성**

```bash
touch reddit_crawler/__init__.py tests/__init__.py
```

- [ ] **Step 6: 의존성 설치**

```bash
pip install -r requirements.txt
```

Expected: 패키지들이 정상 설치됨. `pip show praw trafilatura` 로 확인.

- [ ] **Step 7: 커밋**

```bash
git add requirements.txt .env.example .gitignore reddit_crawler/__init__.py tests/__init__.py
git commit -m "chore: scaffold project structure"
```

---

### Task 2: config.py

**Files:**
- Create: `reddit_crawler/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_config.py`:
```python
import importlib
import os
import sys

import pytest


def reload_config(env_vars: dict):
    """환경변수를 설정하고 config 모듈을 재로드한다."""
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
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'reddit_crawler.config'`

- [ ] **Step 3: config.py 구현**

`reddit_crawler/config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "reddit-crawler/1.0")

SUBREDDITS: list[str] = os.getenv("SUBREDDITS", "cybersecurity,netsec,Malware").split(",")
POSTS_PER_SUBREDDIT: int = int(os.getenv("POSTS_PER_SUBREDDIT", "25"))
CRAWL_INTERVAL_HOURS: int = int(os.getenv("CRAWL_INTERVAL_HOURS", "1"))
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
pytest tests/test_config.py -v
```

Expected: 4개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add reddit_crawler/config.py tests/test_config.py
git commit -m "feat: add config module with env var loading"
```

---

### Task 3: storage.py

**Files:**
- Create: `reddit_crawler/storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_storage.py`:
```python
import json
import re
from pathlib import Path

import pytest

from reddit_crawler.storage import save


@pytest.fixture(autouse=True)
def tmp_data_dir(tmp_path, monkeypatch):
    """data/ 디렉토리를 임시 경로로 교체."""
    import reddit_crawler.storage as storage_mod
    monkeypatch.setattr(storage_mod, "DATA_DIR", tmp_path / "data")
    return tmp_path / "data"


def test_save_creates_file():
    data = {"crawled_at": "2025-05-20T14-00-00", "subreddits": []}
    filepath = save(data)
    assert filepath.exists()


def test_save_filename_format():
    data = {"crawled_at": "2025-05-20T14-00-00", "subreddits": []}
    filepath = save(data)
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json", filepath.name)


def test_save_content_is_valid_json():
    data = {"crawled_at": "2025-05-20T14-00-00", "subreddits": [{"name": "test", "posts": []}]}
    filepath = save(data)
    loaded = json.loads(filepath.read_text(encoding="utf-8"))
    assert loaded == data


def test_save_creates_data_dir_if_missing(tmp_data_dir):
    assert not tmp_data_dir.exists()
    save({"crawled_at": "x", "subreddits": []})
    assert tmp_data_dir.exists()
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
pytest tests/test_storage.py -v
```

Expected: `ImportError: cannot import name 'save' from 'reddit_crawler.storage'`

- [ ] **Step 3: storage.py 구현**

`reddit_crawler/storage.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")


def save(data: dict) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    filepath = DATA_DIR / f"{timestamp}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
pytest tests/test_storage.py -v
```

Expected: 4개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add reddit_crawler/storage.py tests/test_storage.py
git commit -m "feat: add storage module for JSON file output"
```

---

### Task 4: article.py

**Files:**
- Create: `reddit_crawler/article.py`
- Create: `tests/test_article.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_article.py`:
```python
from unittest.mock import MagicMock, patch

import pytest

from reddit_crawler.article import extract_article, is_external_url


# --- is_external_url 테스트 ---

@pytest.mark.parametrize("url,expected", [
    ("https://krebsonsecurity.com/2025/05/attack", True),
    ("https://www.reddit.com/r/cybersecurity/comments/abc", False),
    ("https://redd.it/abc123", False),
    ("https://i.redd.it/image.png", False),
    ("https://v.redd.it/video123", False),
    ("https://www.reddit.com/r/netsec", False),
    ("", False),
])
def test_is_external_url(url, expected):
    assert is_external_url(url) == expected


# --- extract_article 테스트 ---

def test_extract_article_trafilatura_success():
    fake_html = "<html><body><p>Article content</p></body></html>"
    fake_result = {"title": "Test Title", "text": "Article content"}

    with patch("reddit_crawler.article.trafilatura.fetch_url", return_value=fake_html), \
         patch("reddit_crawler.article.trafilatura.bare_extraction", return_value=fake_result):
        result = extract_article("https://example.com/news")

    assert result is not None
    assert result["title"] == "Test Title"
    assert result["content"] == "Article content"
    assert "extracted_at" in result


def test_extract_article_trafilatura_fail_newspaper_success():
    mock_article = MagicMock()
    mock_article.title = "Newspaper Title"
    mock_article.text = "Newspaper content"

    with patch("reddit_crawler.article.trafilatura.fetch_url", return_value=None), \
         patch("reddit_crawler.article.NewspaperArticle", return_value=mock_article):
        result = extract_article("https://example.com/news")

    assert result is not None
    assert result["title"] == "Newspaper Title"
    assert result["content"] == "Newspaper content"


def test_extract_article_both_fail_returns_none():
    with patch("reddit_crawler.article.trafilatura.fetch_url", return_value=None), \
         patch("reddit_crawler.article.NewspaperArticle", side_effect=Exception("fail")):
        result = extract_article("https://example.com/news")

    assert result is None


def test_extract_article_trafilatura_empty_text_falls_back():
    fake_html = "<html></html>"
    fake_result = {"title": "T", "text": ""}  # 빈 텍스트

    mock_article = MagicMock()
    mock_article.title = "NP Title"
    mock_article.text = "NP content"

    with patch("reddit_crawler.article.trafilatura.fetch_url", return_value=fake_html), \
         patch("reddit_crawler.article.trafilatura.bare_extraction", return_value=fake_result), \
         patch("reddit_crawler.article.NewspaperArticle", return_value=mock_article):
        result = extract_article("https://example.com/news")

    assert result["title"] == "NP Title"
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
pytest tests/test_article.py -v
```

Expected: `ImportError: cannot import name 'extract_article' from 'reddit_crawler.article'`

- [ ] **Step 3: article.py 구현**

`reddit_crawler/article.py`:
```python
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
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
pytest tests/test_article.py -v
```

Expected: 8개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add reddit_crawler/article.py tests/test_article.py
git commit -m "feat: add article extractor with trafilatura and newspaper3k fallback"
```

---

### Task 5: crawler.py

**Files:**
- Create: `reddit_crawler/crawler.py`
- Create: `tests/test_crawler.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_crawler.py`:
```python
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reddit_crawler.crawler import (
    _load_state,
    _save_state,
    crawl,
    fetch_posts,
)


def make_submission(id_, title, url, score=10, num_comments=5, created_utc=1716206400.0, selftext=""):
    s = MagicMock()
    s.id = id_
    s.title = title
    s.url = url
    s.score = score
    s.num_comments = num_comments
    s.created_utc = created_utc
    s.selftext = selftext
    return s


# --- state 파일 테스트 ---

def test_load_state_returns_empty_when_no_file(tmp_path, monkeypatch):
    import reddit_crawler.crawler as crawl_mod
    monkeypatch.setattr(crawl_mod, "STATE_FILE", tmp_path / "state.json")
    state = _load_state()
    assert state == {"seen_post_ids": []}


def test_save_and_load_state_roundtrip(tmp_path, monkeypatch):
    import reddit_crawler.crawler as crawl_mod
    monkeypatch.setattr(crawl_mod, "STATE_FILE", tmp_path / "state.json")
    _save_state({"seen_post_ids": ["id1", "id2"], "last_crawled_at": "2025-01-01T00:00:00"})
    state = _load_state()
    assert state["seen_post_ids"] == ["id1", "id2"]


# --- fetch_posts 테스트 ---

def test_fetch_posts_returns_normalized_posts():
    mock_reddit = MagicMock()
    submissions = [make_submission("a1", "Title A", "https://example.com")]
    mock_reddit.subreddit.return_value.new.return_value = iter(submissions)

    posts = fetch_posts("cybersecurity", mock_reddit, seen_ids=set())

    assert len(posts) == 1
    assert posts[0]["id"] == "a1"
    assert posts[0]["title"] == "Title A"
    assert posts[0]["url"] == "https://example.com"
    assert "created_utc" in posts[0]


def test_fetch_posts_skips_seen_ids():
    mock_reddit = MagicMock()
    submissions = [
        make_submission("seen1", "Old post", "https://example.com"),
        make_submission("new1", "New post", "https://example.com/new"),
    ]
    mock_reddit.subreddit.return_value.new.return_value = iter(submissions)

    posts = fetch_posts("cybersecurity", mock_reddit, seen_ids={"seen1"})

    assert len(posts) == 1
    assert posts[0]["id"] == "new1"


def test_fetch_posts_retries_on_praw_exception():
    import praw.exceptions

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.new.side_effect = [
        praw.exceptions.PRAWException("rate limit"),
        praw.exceptions.PRAWException("rate limit"),
        iter([make_submission("a1", "Title", "https://x.com")]),
    ]

    with patch("reddit_crawler.crawler.time.sleep"):
        posts = fetch_posts("cybersecurity", mock_reddit, seen_ids=set())

    assert len(posts) == 1


def test_fetch_posts_returns_empty_after_3_failures():
    import praw.exceptions

    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.new.side_effect = praw.exceptions.PRAWException("fail")

    with patch("reddit_crawler.crawler.time.sleep"):
        posts = fetch_posts("cybersecurity", mock_reddit, seen_ids=set())

    assert posts == []


# --- crawl() 통합 테스트 ---

def test_crawl_updates_seen_ids(tmp_path, monkeypatch):
    import reddit_crawler.crawler as crawl_mod
    monkeypatch.setattr(crawl_mod, "STATE_FILE", tmp_path / "state.json")

    mock_reddit = MagicMock()
    submissions = [make_submission("newid", "Title", "https://x.com")]
    mock_reddit.subreddit.return_value.new.return_value = iter(submissions)

    with patch("reddit_crawler.crawler._make_reddit", return_value=mock_reddit), \
         patch("reddit_crawler.crawler.config.SUBREDDITS", ["cybersecurity"]):
        crawl()

    state = _load_state()
    assert "newid" in state["seen_post_ids"]
```

- [ ] **Step 2: 테스트 실행 — 실패 확인**

```bash
pytest tests/test_crawler.py -v
```

Expected: `ImportError: cannot import name '_load_state' from 'reddit_crawler.crawler'`

- [ ] **Step 3: crawler.py 구현**

`reddit_crawler/crawler.py`:
```python
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import praw
import praw.exceptions

from . import config

logger = logging.getLogger(__name__)

STATE_FILE = Path("state.json")
MAX_SEEN_IDS = 500


def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"seen_post_ids": []}


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _make_reddit() -> praw.Reddit:
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT,
    )


def fetch_posts(subreddit_name: str, reddit: praw.Reddit, seen_ids: set) -> list[dict]:
    for attempt in range(3):
        try:
            posts = []
            for submission in reddit.subreddit(subreddit_name).new(limit=config.POSTS_PER_SUBREDDIT):
                if submission.id in seen_ids:
                    continue
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "url": submission.url,
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "created_utc": datetime.fromtimestamp(
                        submission.created_utc, tz=timezone.utc
                    ).isoformat(),
                    "selftext": submission.selftext,
                })
            return posts
        except praw.exceptions.PRAWException as e:
            logger.warning("Attempt %d/3 failed for r/%s: %s", attempt + 1, subreddit_name, e)
            if attempt < 2:
                time.sleep(2 ** attempt)
    logger.error("Failed to fetch r/%s after 3 attempts", subreddit_name)
    return []


def crawl() -> dict:
    state = _load_state()
    seen_ids = set(state.get("seen_post_ids", []))
    reddit = _make_reddit()

    crawled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    result: dict = {"crawled_at": crawled_at, "subreddits": []}
    new_ids: list[str] = []

    for subreddit_name in config.SUBREDDITS:
        posts = fetch_posts(subreddit_name, reddit, seen_ids)
        new_ids.extend(p["id"] for p in posts)
        result["subreddits"].append({"name": subreddit_name, "posts": posts})
        logger.info("Fetched %d new posts from r/%s", len(posts), subreddit_name)

    all_ids = list(seen_ids) + new_ids
    state["seen_post_ids"] = all_ids[-MAX_SEEN_IDS:]
    state["last_crawled_at"] = crawled_at
    _save_state(state)

    return result
```

- [ ] **Step 4: 테스트 실행 — 통과 확인**

```bash
pytest tests/test_crawler.py -v
```

Expected: 8개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add reddit_crawler/crawler.py tests/test_crawler.py
git commit -m "feat: add Reddit crawler with PRAW and duplicate filtering"
```

---

### Task 6: scheduler.py + main.py

**Files:**
- Create: `reddit_crawler/scheduler.py`
- Create: `main.py`

(scheduler는 APScheduler 이벤트 루프를 감싸므로 유닛 테스트 대신 smoke test로 대체)

- [ ] **Step 1: scheduler.py 작성**

`reddit_crawler/scheduler.py`:
```python
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
        next_run_time=datetime.now(),  # 시작 즉시 1회 실행
    )
    logger.info(
        "Scheduler started. Crawling every %d hour(s). Press Ctrl+C to stop.",
        config.CRAWL_INTERVAL_HOURS,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
```

- [ ] **Step 2: main.py 작성**

`main.py`:
```python
import logging
import logging.handlers
from pathlib import Path

from reddit_crawler.scheduler import start

LOG_DIR = Path("logs")


def setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(),
        logging.handlers.TimedRotatingFileHandler(
            LOG_DIR / "crawler.log",
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        ),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


if __name__ == "__main__":
    setup_logging()
    start()
```

- [ ] **Step 3: smoke test — 단 1회만 실행되는지 확인**

`.env` 파일이 준비된 상태에서 아래를 실행. 즉시 크롤링 1회 수행 후 1시간 대기 상태로 진입한다. Ctrl+C로 종료.

```bash
python main.py
```

Expected 출력 (예시):
```
2025-05-20 14:00:00,000 [INFO] reddit_crawler.scheduler: Crawl started
2025-05-20 14:00:01,000 [INFO] reddit_crawler.crawler: Fetched N new posts from r/cybersecurity
2025-05-20 14:00:01,500 [INFO] reddit_crawler.crawler: Fetched N new posts from r/netsec
2025-05-20 14:00:02,000 [INFO] reddit_crawler.crawler: Fetched N new posts from r/Malware
2025-05-20 14:00:15,000 [INFO] reddit_crawler.scheduler: Crawl complete — N posts saved to data/2025-05-20T14-00-15.json
```

- [ ] **Step 4: data/ 디렉토리에 JSON 파일 생성됐는지 확인**

```bash
ls data/
cat data/*.json | python -m json.tool | head -50
```

Expected: `data/2025-05-20T14-00-15.json` 파일이 존재하고 유효한 JSON.

- [ ] **Step 5: 커밋**

```bash
git add reddit_crawler/scheduler.py main.py
git commit -m "feat: add scheduler and main entry point with rotating log"
```

---

### Task 7: lambda_handler.py stub

**Files:**
- Create: `reddit_crawler/lambda_handler.py`

- [ ] **Step 1: lambda_handler.py 작성**

`reddit_crawler/lambda_handler.py`:
```python
import logging

from .article import extract_article, is_external_url
from .crawler import crawl
from .storage import save

logger = logging.getLogger(__name__)


def handler(event: dict, context) -> dict:
    """
    AWS Lambda entry point.
    현재는 로컬 storage.py와 동일하게 /tmp/data/에 저장.
    추후 S3 저장으로 교체 예정.
    """
    import tempfile
    import reddit_crawler.storage as storage_mod
    from pathlib import Path

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
```

- [ ] **Step 2: import 오류 없는지 확인**

```bash
python -c "from reddit_crawler.lambda_handler import handler; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: 커밋**

```bash
git add reddit_crawler/lambda_handler.py
git commit -m "feat: add Lambda handler stub"
```

---

### Task 8: 전체 테스트 스위트 실행

- [ ] **Step 1: 전체 테스트 실행**

```bash
pytest tests/ -v
```

Expected: 전체 테스트 PASS (test_config 4개 + test_storage 4개 + test_article 5개 + test_crawler 8개 = 21개)

- [ ] **Step 2: .gitignore 동작 확인**

```bash
git status
```

Expected: `data/`, `logs/`, `state.json`, `.env`가 untracked으로 표시되지 않음.

- [ ] **Step 3: 최종 커밋**

```bash
git add .
git commit -m "chore: verify all tests pass"
```
