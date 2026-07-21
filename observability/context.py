from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import Iterator


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str | None = None
    request_id: str | None = None
    thread_id: str | None = None
    event_id: str | None = None
    candidate_id: str | None = None
    investigation_id: str | None = None
    approval_request_id: str | None = None
    publication_id: str | None = None


_CONTEXT: ContextVar[TraceContext | None] = ContextVar("revenue_poc_trace_context", default=None)


def current_context() -> TraceContext | None:
    return _CONTEXT.get()


@contextmanager
def trace_context(context: TraceContext | None = None, **values: str | None) -> Iterator[TraceContext]:
    base = context or current_context()
    if base is None:
        raise ValueError("trace_context_requires_trace")
    token = _CONTEXT.set(replace(base, **{key: value for key, value in values.items() if value is not None}))
    try:
        yield _CONTEXT.get()  # type: ignore[misc]
    finally:
        _CONTEXT.reset(token)
