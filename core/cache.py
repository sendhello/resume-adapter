import hashlib
import os

import orjson

CACHE_DIR = "cache"


def _cache_path(prompt: str, text: str) -> str:
    key = hashlib.sha256((prompt + text).encode()).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"{key}.json")


def read_cache(prompt: str, text: str) -> str | None:
    path = _cache_path(prompt, text)
    try:
        with open(path, "rb") as f:
            result = orjson.loads(f.read())
            return result if result else None
    except (FileNotFoundError, orjson.JSONDecodeError):
        return None


def write_cache(prompt: str, text: str, result: str) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(prompt, text)
    with open(path, "wb") as f:
        f.write(orjson.dumps(result))
