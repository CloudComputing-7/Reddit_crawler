import pytest

from reddit_crawler.schema import _extract_cves, _make_id, normalize_reddit_post


def make_post(
    id_="abc123",
    title="Test Post",
    url="https://example.com/article",
    score=10,
    num_comments=3,
    selftext="",
    created_utc="2026-05-20T11:03:41+00:00",
):
    return {
        "id": id_,
        "title": title,
        "url": url,
        "score": score,
        "num_comments": num_comments,
        "selftext": selftext,
        "created_utc": created_utc,
    }


# --- _extract_cves ---

def test_extract_cves_finds_standard_cve():
    assert _extract_cves("Patch for CVE-2024-12345 released") == ["CVE-2024-12345"]


def test_extract_cves_deduplicates():
    assert _extract_cves("CVE-2024-1111 and CVE-2024-1111") == ["CVE-2024-1111"]


def test_extract_cves_multiple():
    result = _extract_cves("CVE-2024-0001 CVE-2023-99999")
    assert result == ["CVE-2024-0001", "CVE-2023-99999"]


def test_extract_cves_case_insensitive():
    result = _extract_cves("cve-2024-1234")
    assert result == ["CVE-2024-1234"]


def test_extract_cves_none():
    assert _extract_cves("no vulnerabilities here") == []


# --- _make_id ---

def test_make_id_is_deterministic():
    assert _make_id("reddit", "abc") == _make_id("reddit", "abc")


def test_make_id_differs_by_source():
    assert _make_id("reddit", "abc") != _make_id("github", "abc")


def test_make_id_is_32_chars():
    assert len(_make_id("reddit", "abc")) == 32


# --- normalize_reddit_post ---

def test_normalize_basic_shape():
    post = make_post()
    item = normalize_reddit_post(post, "cybersecurity")

    assert item["source"] == "reddit"
    assert item["source_id"] == "abc123"
    assert item["source_url"] == "https://www.reddit.com/r/cybersecurity/comments/abc123/"
    assert item["title"] == "Test Post"
    assert item["summary"] is None
    assert item["language"] == "en"
    assert item["published_at"] == post["created_utc"]
    assert item["updated_at"] is None
    assert item["due_date"] is None


def test_normalize_severity_unknown():
    item = normalize_reddit_post(make_post(), "cybersecurity")
    assert item["severity"]["label"] == "unknown"
    assert item["severity"]["cvss_score"] is None


def test_normalize_identifiers_empty_by_default():
    item = normalize_reddit_post(make_post(), "cybersecurity")
    assert item["identifiers"]["cve_ids"] == []
    assert item["identifiers"]["kev_listed"] is False
    assert item["identifiers"]["ransomware_known"] is False


def test_normalize_cve_extracted_from_title():
    post = make_post(title="Critical CVE-2024-99999 in OpenSSL")
    item = normalize_reddit_post(post, "netsec")
    assert "CVE-2024-99999" in item["identifiers"]["cve_ids"]
    assert "vulnerability" in item["tags"]["categories"]


def test_normalize_no_cve_category_is_discussion():
    post = make_post(title="Weekly security news")
    item = normalize_reddit_post(post, "cybersecurity")
    assert item["tags"]["categories"] == ["discussion"]


def test_normalize_external_url_in_references():
    post = make_post(url="https://example.com/news")
    item = normalize_reddit_post(post, "cybersecurity")
    urls = [r["url"] for r in item["action"]["references"]]
    assert "https://example.com/news" in urls


def test_normalize_content_raw_from_article():
    post = make_post(selftext="short selftext")
    article = {"content": "Full article body text", "title": "Article Title"}
    item = normalize_reddit_post(post, "cybersecurity", article=article)
    assert item["content_raw"] == "Full article body text"


def test_normalize_content_raw_falls_back_to_selftext():
    post = make_post(selftext="Discussion body here")
    item = normalize_reddit_post(post, "cybersecurity", article=None)
    assert item["content_raw"] == "Discussion body here"


def test_normalize_id_is_deterministic():
    post = make_post(id_="xyz789")
    item1 = normalize_reddit_post(post, "netsec")
    item2 = normalize_reddit_post(post, "netsec")
    assert item1["id"] == item2["id"]


def test_normalize_audience_structure():
    item = normalize_reddit_post(make_post(), "cybersecurity")
    audience = item["audience"]
    assert "general" in audience["scores"]
    assert "developer" in audience["scores"]
    assert "security" in audience["scores"]
    assert audience["primary"] == "security"
    assert 0 <= audience["confidence"] <= 1
