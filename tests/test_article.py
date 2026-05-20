from unittest.mock import MagicMock, patch

import pytest

from reddit_crawler.article import extract_article, is_external_url


@pytest.mark.parametrize("url,expected", [
    ("https://krebsonsecurity.com/2025/05/attack", True),
    ("https://www.reddit.com/r/cybersecurity/comments/abc", False),
    ("https://redd.it/abc123", False),
    ("https://i.redd.it/image.png", False),
    ("https://v.redd.it/video123", False),
    ("https://old.reddit.com/r/netsec", False),
    ("", False),
])
def test_is_external_url(url, expected):
    assert is_external_url(url) == expected


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


def test_extract_article_empty_text_falls_back():
    fake_html = "<html></html>"
    fake_result = {"title": "T", "text": ""}

    mock_article = MagicMock()
    mock_article.title = "NP Title"
    mock_article.text = "NP content"

    with patch("reddit_crawler.article.trafilatura.fetch_url", return_value=fake_html), \
         patch("reddit_crawler.article.trafilatura.bare_extraction", return_value=fake_result), \
         patch("reddit_crawler.article.NewspaperArticle", return_value=mock_article):
        result = extract_article("https://example.com/news")

    assert result["title"] == "NP Title"
