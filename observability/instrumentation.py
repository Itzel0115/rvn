from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from .tracing import get_recorder


@contextmanager
def instrument(name: str, *, attributes: dict[str, Any] | None = None, failure_category: str | None = None) -> Iterator[Any]:
    """Safe no-op instrumentation boundary usable by Phase 1–3 code."""
    with get_recorder().span(name, attributes=attributes, failure_category=failure_category) as span:
        yield span
