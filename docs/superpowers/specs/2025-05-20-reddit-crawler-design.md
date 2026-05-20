# Reddit Crawler — Design Spec

**Date:** 2025-05-20  
**Status:** Approved

---

## Overview

보안 관련 서브레딧(r/cybersecurity, r/netsec, r/Malware)의 최신 게시물을 1시간마다 크롤링하여 JSON으로 저장하는 Python 프로그램. 로컬 실행 버전을 우선 구현하며, AWS Lambda 포팅을 고려한 모듈형 구조로 설계한다.

---

## Architecture

### 데이터 흐름

```
APScheduler (1시간마다)
    │
    ▼
crawler.py ──→ Reddit API (PRAW)
    │              r/cybersecurity, r/netsec, r/Malware
    │              최신 게시물 25개/서브레딧
    ▼
article.py ──→ 외부 뉴스 URL 감지 → trafilatura로 본문 추출
    │              (reddit.com, redd.it, i.redd.it 내부 링크는 스킵)
    │              실패 시 newspaper3k로 fallback
    ▼
storage.py ──→ data/YYYY-MM-DDTHH:MM:SS.json 저장
```

### 프로젝트 구조

```
reddit-crawler/
  reddit_crawler/
    __init__.py
    config.py          # 환경변수 & 설정값 로드
    crawler.py         # PRAW로 Reddit 게시물 수집
    article.py         # 뉴스 링크 본문 추출
    storage.py         # JSON 파일 저장
    scheduler.py       # APScheduler 로컬 실행
    lambda_handler.py  # Lambda entry point (stub)
  data/                # 크롤링 결과 JSON (gitignore)
  logs/                # 로그 파일 (gitignore)
  state.json           # 중복 방지용 상태 파일 (gitignore)
  .env                 # API 키 (gitignore)
  .env.example         # API 키 템플릿
  requirements.txt
  main.py              # 로컬 실행 진입점
```

---

## Data Model

### 출력 JSON 스키마

파일명: `data/2025-05-20T14-00-00.json`

```json
{
  "crawled_at": "2025-05-20T14:00:00",
  "subreddits": [
    {
      "name": "cybersecurity",
      "posts": [
        {
          "id": "abc123",
          "title": "New zero-day vulnerability...",
          "url": "https://example.com/article",
          "score": 342,
          "num_comments": 45,
          "created_utc": "2025-05-20T13:12:00",
          "selftext": "",
          "article": {
            "title": "New zero-day vulnerability...",
            "content": "Full article text here...",
            "extracted_at": "2025-05-20T14:00:05"
          }
        }
      ]
    }
  ]
}
```

- `article` 필드: 외부 뉴스 링크 게시물에만 포함
- 추출 실패 시: `"article": null`
- 내부 링크(self post, 이미지 등): `"article"` 필드 없음

### 상태 파일 (`state.json`)

중복 수집 방지용. 실행마다 갱신.

```json
{
  "last_crawled_at": "2025-05-20T14:00:00",
  "seen_post_ids": ["abc123", "def456"]
}
```

- `seen_post_ids`: 최근 500개 ID만 유지 (오래된 것 자동 제거)
- 첫 실행 시 파일 없으면 전체 수집

---

## Module Details

### `config.py`

- `python-dotenv`로 `.env` 파일 로드
- 설정값 상수로 노출:
  - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
  - `SUBREDDITS: list[str]` (기본: `["cybersecurity", "netsec", "Malware"]`)
  - `POSTS_PER_SUBREDDIT: int` (기본: 25)
  - `CRAWL_INTERVAL_HOURS: int` (기본: 1)

### `crawler.py`

- PRAW `Reddit` 인스턴스로 각 서브레딧 `new` 피드 수집
- `state.json`에서 `seen_post_ids` 로드 → 이미 수집한 게시물 스킵
- 수집 후 `seen_post_ids` 갱신 (최대 500개 유지)
- Rate limit 초과 시 최대 3회 재시도 (지수 백오프)
- 반환: `list[dict]` (정규화된 게시물)

### `article.py`

- 외부 URL 판별 함수: `reddit.com`, `redd.it`, `i.redd.it`, `self.*` 도메인은 `None` 반환
- 추출 순서:
  1. trafilatura (`fetch_url` + `extract`)
  2. 실패 시 newspaper3k (`Article`)
- 타임아웃: 10초
- 실패 시 `None` 반환 (예외를 상위로 전파하지 않음)

### `storage.py`

- `data/` 디렉토리 없으면 자동 생성
- 파일명: `data/{ISO_TIMESTAMP}.json` (`:`는 `-`로 치환하여 파일명 안전하게)
- UTF-8 인코딩, `ensure_ascii=False`, `indent=2`

### `scheduler.py`

- `APScheduler.BlockingScheduler` 사용
- 시작 즉시 1회 실행 후 매 1시간마다 반복
- `Ctrl+C` → graceful shutdown

### `lambda_handler.py` (stub)

- `handler(event, context)` 시그니처만 정의
- 내부에서 `crawler.py`, `article.py`, `storage.py` 임포트 후 동일 로직 호출
- Lambda 환경에서는 `data/` 대신 S3 저장으로 교체 예정 (이번 스코프 외)

---

## Error Handling

| 상황 | 처리 방식 |
|------|-----------|
| Reddit API rate limit | 최대 3회 재시도 (지수 백오프), 실패 시 해당 서브레딧 스킵 |
| 뉴스 기사 추출 실패 | `article: null` 저장, 게시물은 보존 |
| 파일 저장 실패 | 에러 로그 출력, 다음 사이클 대기 |
| 네트워크 타임아웃 | 뉴스 요청 10초 제한 |

모든 에러는 `logs/crawler.log`에 기록. RotatingFileHandler, 최대 7일치 보존.

---

## Configuration (`.env.example`)

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=reddit-crawler/1.0 by u/yourusername

SUBREDDITS=cybersecurity,netsec,Malware
POSTS_PER_SUBREDDIT=25
CRAWL_INTERVAL_HOURS=1
```

---

## Dependencies

```
praw>=7.7
trafilatura>=1.6
newspaper3k>=0.2
apscheduler>=3.10
python-dotenv>=1.0
requests>=2.31
```

---

## Out of Scope (이번 구현)

- AWS Lambda 실제 배포
- S3 저장 연동
- 데이터 중복 제거 고도화 (DB 기반)
- 알림 기능 (Slack, 이메일 등)
