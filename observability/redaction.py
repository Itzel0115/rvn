from __future__ import annotations

import hashlib
import math
import re
from typing import Any

SENSITIVE_KEYS = {"api_key", "token", "password", "secret", "authorization", "cookie", "connection_string", "database_url", "private_key"}
_PATH = re.compile(r"(?:[A-Za-z]:\\|/)(?:[^\s'\"]+)")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def detect_sensitive_key(key: object) -> bool:
    lowered = str(key).lower().replace("-", "_")
    return any(item in lowered for item in SENSITIVE_KEYS)


def hash_content(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8", "replace")).hexdigest()


def truncate_value(value: object, limit: int = 512) -> str:
    text = _CONTROL.sub("", str(value)).replace("\n", " ").replace("\r", " ")
    return text[:limit] + ("…" if len(text) > limit else "")


def redact_text(value: object, limit: int = 512) -> str:
    text = truncate_value(value, limit)
    return _PATH.sub("<path-redacted>", text)


def sanitize_exception(exc: BaseException | object) -> str:
    return redact_text(str(exc), 256)


def redact_mapping(value: Any, *, capture_content: bool = False, limit: int = 512, depth: int = 0) -> Any:
    if depth > 5:
        return "<truncated-depth>"
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (int,)):
        return value
    if isinstance(value, str):
        return redact_text(value, limit) if capture_content else {"content_hash": hash_content(value), "length": len(value)}
    if isinstance(value, dict):
        return {str(key): "<redacted>" if detect_sensitive_key(key) else redact_mapping(item, capture_content=capture_content, limit=limit, depth=depth + 1) for key, item in list(value.items())[:50]}
    if isinstance(value, (list, tuple, set)):
        return [redact_mapping(item, capture_content=capture_content, limit=limit, depth=depth + 1) for item in list(value)[:20]]
    return redact_text(type(value).__name__, limit)
