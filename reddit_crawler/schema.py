import hashlib
import re
from datetime import datetime, timezone

CVE_RE = re.compile(r'\bCVE-\d{4}-\d{4,7}\b', re.IGNORECASE)


def _make_id(source: str, source_id: str) -> str:
    return hashlib.sha256(f"{source}:{source_id}".encode()).hexdigest()[:32]


def _extract_cves(text: str) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for cve in CVE_RE.findall(text):
        upper = cve.upper()
        if upper not in seen:
            seen.add(upper)
            result.append(upper)
    return result


def normalize_reddit_post(post: dict, subreddit: str, article: dict | None = None) -> dict:
    post_id = post["id"]
    reddit_url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"
    external_url = post.get("url", "")

    if article and article.get("content"):
        content_raw = article["content"]
    else:
        content_raw = post.get("selftext", "") or ""

    cve_ids = _extract_cves(f"{post['title']} {post.get('selftext', '')} {content_raw}")

    categories = ["discussion"]
    if cve_ids:
        categories.append("vulnerability")

    references = []
    if external_url and external_url != reddit_url:
        references.append({"label": "Source", "url": external_url})

    return {
        "id": _make_id("reddit", post_id),
        "source": "reddit",
        "source_id": post_id,
        "source_url": reddit_url,

        "title": post["title"],
        "summary": None,
        "content_raw": content_raw,
        "language": "en",

        "published_at": post["created_utc"],
        "updated_at": None,
        "due_date": None,

        "severity": {
            "label": "unknown",
            "cvss_score": None,
            "cvss_vector": None,
            "epss_score": None,
        },

        "affected": [],

        "identifiers": {
            "cve_ids": cve_ids,
            "ghsa_id": None,
            "kev_listed": False,
            "ransomware_known": False,
        },

        "tags": {
            "categories": categories,
            "cwe": [],
            "attack_vectors": [],
            "tech_stack": [],
            "topics": [],
        },

        "action": {
            "required_action": None,
            "remediation": None,
            "references": references,
        },

        "audience": {
            "scores": {
                "general": 0,
                "developer": 0,
                "security": 0,
            },
            "primary": "security",
            "confidence": 0,
            "recommended_for": [],
        },
    }
