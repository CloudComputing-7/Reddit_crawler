import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")


def save(items: list[dict], crawled_at: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    filepath = DATA_DIR / f"{timestamp}.json"
    output = {
        "crawled_at": crawled_at,
        "source": "reddit",
        "count": len(items),
        "items": items,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return filepath
