import json
import re

import pytest

from reddit_crawler.storage import save


@pytest.fixture(autouse=True)
def tmp_data_dir(tmp_path, monkeypatch):
    import reddit_crawler.storage as storage_mod
    monkeypatch.setattr(storage_mod, "DATA_DIR", tmp_path / "data")
    return tmp_path / "data"


def test_save_creates_file():
    filepath = save({"crawled_at": "2025-05-20T14-00-00", "subreddits": []})
    assert filepath.exists()


def test_save_filename_format():
    filepath = save({"crawled_at": "x", "subreddits": []})
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json", filepath.name)


def test_save_content_roundtrip():
    data = {"crawled_at": "x", "subreddits": [{"name": "test", "posts": []}]}
    filepath = save(data)
    assert json.loads(filepath.read_text(encoding="utf-8")) == data


def test_save_creates_data_dir_if_missing(tmp_data_dir):
    assert not tmp_data_dir.exists()
    save({"crawled_at": "x", "subreddits": []})
    assert tmp_data_dir.exists()
