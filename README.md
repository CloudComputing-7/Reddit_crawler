# Reddit Crawler

보안 관련 Reddit 커뮤니티(r/cybersecurity, r/netsec, r/Malware)의 최신 게시물을 주기적으로 수집하고, 외부 링크가 포함된 게시물은 본문 전체를 추출하여 통합 스키마 형식의 JSON으로 저장하는 크롤러입니다.

---

## 주요 기능

- **Reddit JSON 엔드포인트 사용** — API 키 없이 `reddit.com/r/{sub}/new.json` 직접 호출
- **중복 방지** — `state.json`에 최근 500개 게시물 ID를 저장하여 재수집 방지
- **기사 본문 추출** — 외부 URL 포함 게시물은 trafilatura(1차) → newspaper3k(fallback)로 전문 추출
- **통합 스키마 출력** — CVE 자동 추출, 심각도·태그·액션 필드 포함 구조화된 JSON
- **로컬 스케줄러** — APScheduler 기반으로 설정한 주기마다 자동 실행
- **AWS Lambda 호환** — `lambda_handler.handler` 진입점 제공

---

## 프로젝트 구조

```
reddit-crawler/
├── main.py                        # 로컬 실행 진입점 (스케줄러 시작)
├── requirements.txt
├── .env                           # 환경변수 (git 제외)
├── .env.example                   # 환경변수 예시
├── state.json                     # 수집한 게시물 ID 캐시 (자동 생성)
├── data/                          # 크롤링 결과 JSON 저장 디렉토리
├── logs/                          # 로그 파일 (자동 생성)
└── reddit_crawler/
    ├── config.py                  # 환경변수 로드
    ├── crawler.py                 # Reddit 게시물 수집
    ├── article.py                 # 외부 기사 본문 추출
    ├── schema.py                  # 통합 스키마 정규화
    ├── storage.py                 # JSON 파일 저장
    ├── scheduler.py               # APScheduler 기반 스케줄러
    └── lambda_handler.py          # AWS Lambda 핸들러
```

---

## 설치

Python **3.10** 이상 필요 (3.12+ 환경에서는 `python3.10` 명시 권장).

```bash
git clone https://github.com/CloudComputing-7/Reddit_crawler.git
cd Reddit_crawler
pip install -r requirements.txt
```

---

## 환경변수 설정

`.env.example`을 복사하여 `.env`를 생성합니다.

```bash
cp .env.example .env
```

| 변수명 | 설명 | 기본값 |
|---|---|---|
| `REDDIT_USER_AGENT` | Reddit 요청 시 사용할 User-Agent | `reddit-crawler/1.0` |
| `SUBREDDITS` | 크롤링할 서브레딧 (쉼표 구분) | `cybersecurity,netsec,Malware` |
| `POSTS_PER_SUBREDDIT` | 서브레딧당 최대 수집 게시물 수 | `25` |
| `CRAWL_INTERVAL_HOURS` | 크롤링 주기 (시간) | `1` |

Reddit 차단을 피하려면 `REDDIT_USER_AGENT`를 브라우저 형태로 설정하는 것을 권장합니다.

```env
REDDIT_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36
```

---

## 로컬 실행

### 스케줄러 시작 (권장)

설정한 주기마다 자동으로 크롤링합니다. 시작 즉시 1회 실행됩니다.

```bash
python3.10 main.py
```

로그는 콘솔과 `logs/crawler.log`에 동시에 출력되며, 자정마다 롤링됩니다(최대 7일 보관).

### 1회만 실행

```bash
python3.10 -c "
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
from reddit_crawler.scheduler import run_crawl
run_crawl()
"
```

### 결과 확인

수집 결과는 `data/` 디렉토리에 `YYYY-MM-DDTHH-MM-SS.json` 형식으로 저장됩니다.

```bash
ls data/
cat data/2026-05-23T15-10-00.json | python3.10 -m json.tool | head -60
```

---

## AWS Lambda 실행

### 핸들러 설정

Lambda 함수 핸들러를 아래와 같이 지정합니다.

```
reddit_crawler.lambda_handler.handler
```

결과는 `/tmp/reddit-crawler-data/` 에 저장됩니다 (추후 S3로 교체 예정).

### 배포 패키지 생성

```bash
pip install -r requirements.txt -t package/
cp -r reddit_crawler package/
cd package && zip -r ../lambda.zip . && cd ..
zip lambda.zip main.py
```

### 환경변수

Lambda 콘솔 또는 SAM/CDK에서 아래 환경변수를 설정합니다.

```
REDDIT_USER_AGENT=...
SUBREDDITS=cybersecurity,netsec,Malware
POSTS_PER_SUBREDDIT=25
```

### 이벤트 예시

트리거 없이 수동 테스트할 때 사용하는 빈 이벤트입니다.

```json
{}
```

---

## 출력 데이터 구조

파일 하나당 한 번의 크롤링 결과를 담습니다.

```json
{
  "crawled_at": "2026-05-23T15-10-00",
  "source": "reddit",
  "count": 37,
  "items": [
    {
      "id": "d73b1c8f...",
      "source": "reddit",
      "source_id": "abc123",
      "source_url": "https://www.reddit.com/r/cybersecurity/comments/abc123/",
      "title": "Critical CVE-2026-99999 in OpenSSL",
      "summary": null,
      "content_raw": "기사 본문 또는 selftext",
      "language": "en",
      "published_at": "2026-05-23T10:00:00+00:00",
      "updated_at": null,
      "due_date": null,
      "severity": {
        "label": "unknown",
        "cvss_score": null,
        "cvss_vector": null,
        "epss_score": null
      },
      "affected": [],
      "identifiers": {
        "cve_ids": ["CVE-2026-99999"],
        "ghsa_id": null,
        "kev_listed": false,
        "ransomware_known": false
      },
      "tags": {
        "categories": ["discussion", "vulnerability"],
        "cwe": [],
        "attack_vectors": [],
        "tech_stack": [],
        "topics": []
      },
      "action": {
        "required_action": null,
        "remediation": null,
        "references": [
          { "label": "Source", "url": "https://example.com/article" }
        ]
      },
      "audience": {
        "scores": { "general": 0, "developer": 0, "security": 0 },
        "primary": "security",
        "confidence": 0,
        "recommended_for": []
      }
    }
  ]
}
```

`summary`, `severity`, `affected`, `tags.tech_stack`, `audience.scores` 등 LLM 후처리가 필요한 필드는 현재 기본값(null / 0)으로 저장됩니다.

---

## 테스트

```bash
python3.10 -m pytest tests/ -v
```

총 46개의 테스트가 포함되어 있습니다 (crawler, article, schema, storage, config).
