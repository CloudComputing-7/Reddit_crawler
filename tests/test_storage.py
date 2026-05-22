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
    filepath = save([], "2025-05-20T14-00-00")
    assert filepath.exists()


def test_save_filename_format():
    filepath = save([], "x")
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json", filepath.name)


def test_save_content_roundtrip():
    items = [{"id": "abc", "source": "reddit"}]
    filepath = save(items, "2025-05-20T14-00-00")
    result = json.loads(filepath.read_text(encoding="utf-8"))
    assert result["crawled_at"] == "2025-05-20T14-00-00"
    assert result["source"] == "reddit"
    assert result["count"] == 1
    assert result["items"] == items


def test_save_creates_data_dir_if_missing(tmp_data_dir):
    assert not tmp_data_dir.exists()
    save([], "x")
    assert tmp_data_dir.exists()
