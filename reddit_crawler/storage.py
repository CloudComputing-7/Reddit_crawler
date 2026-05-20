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
