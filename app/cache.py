"""
Tiny file-based cache for PR reviews.
A PR that was reviewed successfully once is served from disk afterwards,
so repeat views cost zero API calls.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional

CACHE_DIR = Path("cache")


def _path_for(key: str) -> Path:
    digest = hashlib.sha256(key.strip().rstrip("/").encode()).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.json"


def load_cached(key: str) -> Optional[dict]:
    path = _path_for(key)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_cached(key: str, data: dict) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    _path_for(key).write_text(json.dumps(data), encoding="utf-8")