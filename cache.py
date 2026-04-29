import os
import re
import json
import time
import hashlib
from urllib.parse import urlparse

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_TTL = 300  # seconds


def _cache_filename(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "unknown").replace("www.", "")
    slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", (parsed.path + parsed.query)).strip("_")
    slug = re.sub(r"_+", "_", slug)[:60]
    short = hashlib.md5(url.encode()).hexdigest()[:8]
    name = f"{host}_{slug}_{short}" if slug else f"{host}_{short}"
    return os.path.join(CACHE_DIR, f"{name}.json")


def cache_get(url: str):
    path = _cache_filename(url)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if time.time() - entry.get("timestamp", 0) > CACHE_TTL:
        os.remove(path)
        return None
    return entry.get("content")


def cache_set(url: str, content: str):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_filename(url)
    entry = {
        "url": url,
        "timestamp": time.time(),
        "content": content,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
