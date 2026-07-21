from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

from .config import ObservabilityConfig, get_config
from .context import TraceContext, _CONTEXT, current_context
from .models import SpanRecord, TraceEvent, TraceRun, utc_now
from .redaction import redact_mapping, sanitize_exception
from .store import SQLiteTraceStore


class TraceRecorder:
    def __init__(self, config: ObservabilityConfig | None = None, store: SQLiteTraceStore | None = None) -> None:
        self.config = config or get_config(); self.store = store

    @property
    def enabled(self) -> bool: return self.config.enabled and self.config.store_backend == "sqlite"

    def start_run(self, operation_name: str, *, request_id: str | None = None, runtime_mode: str | None = None, **links: str | None) -> TraceRun | None:
        if not self.enabled: return None
        trace_id, root_span_id = uuid.uuid4().hex, uuid.uuid4().hex[:16]
        trace = TraceRun(trace_id=trace_id, root_span_id=root_span_id, request_id=request_id, operation_name=operation_name, runtime_mode=runtime_mode, content_capture_enabled=self.config.capture_content, **{key: value for key, value in links.items() if key in {"thread_id", "event_id", "candidate_id", "investigation_id"}})
        self._safe_save_trace(trace)
        return trace

    @contextmanager
    def run(self, operation_name: str, *, request_id: str | None = None, runtime_mode: str | None = None, **links: str | None) -> Iterator[TraceRun | None]:
        trace = self.start_run(operation_name, request_id=request_id, runtime_mode=runtime_mode, **links)
        if trace is None:
            yield None; return
        token = _CONTEXT.set(TraceContext(trace_id=trace.trace_id, span_id=trace.root_span_id, request_id=request_id, thread_id=trace.thread_id, event_id=trace.event_id, candidate_id=trace.candidate_id, investigation_id=trace.investigation_id))
        try:
            with self.span(operation_name, span_id=trace.root_span_id, parent_span_id=None): yield trace
            trace.status = "completed"; trace.final_status = "completed"
        except Exception as exc:
            trace.status = "failed"; trace.final_status = "failed"; trace.failure_category = "unknown_failure"; raise
        finally:
            trace.finished_at = utc_now(); trace.duration_ms = _duration(trace.started_at, trace.finished_at); self._safe_save_trace(trace); _CONTEXT.reset(token)

    @contextmanager
    def span(self, name: str, *, attributes: dict[str, Any] | None = None, span_id: str | None = None, parent_span_id: str | None = None, failure_category: str | None = None) -> Iterator[SpanRecord | None]:
        context = current_context()
        if not self.enabled or context is None:
            yield None; return
        record = SpanRecord(trace_id=context.trace_id, span_id=span_id or uuid.uuid4().hex[:16], parent_span_id=parent_span_id if parent_span_id is not None else context.span_id, span_name=name, attributes=_safe_attributes(attributes or {}, self.config))
        token = _CONTEXT.set(TraceContext(**{**context.__dict__, "span_id": record.span_id}))
        try:
            yield record; record.status = "ok"
        except Exception as exc:
            record.status = "error"; record.error_type = type(exc).__name__; record.error_message_safe = sanitize_exception(exc); record.failure_category = failure_category or "unknown_failure"; raise
        finally:
            record.finished_at = utc_now(); record.duration_ms = _duration(record.started_at, record.finished_at); self._safe_save_span(record); _CONTEXT.reset(token)

    def event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        # Events are persisted as lightweight standalone span records to keep the SQLite schema compact.
        with self.span(name, attributes=attributes) as span:
            if span is not None: span.events.append(TraceEvent(name, attributes=span.attributes))

    def finish_run(self, trace: TraceRun | None, *, status: str, stop_reason: str | None = None, failure_category: str | None = None, counters: dict[str, int] | None = None) -> None:
        if trace is None: return
        trace.status = status; trace.final_status = status; trace.stop_reason = stop_reason; trace.failure_category = failure_category
        for key, value in (counters or {}).items():
            if hasattr(trace, key): setattr(trace, key, value)
        trace.finished_at = utc_now(); trace.duration_ms = _duration(trace.started_at, trace.finished_at); self._safe_save_trace(trace)

    def _safe_save_trace(self, trace: TraceRun) -> None:
        try: (self.store or SQLiteTraceStore(self.config.database_path)).save_trace(trace)
        except Exception: pass
    def _safe_save_span(self, span: SpanRecord) -> None:
        try: (self.store or SQLiteTraceStore(self.config.database_path)).save_span(span)
        except Exception: pass


def _safe_attributes(attributes: dict[str, Any], config: ObservabilityConfig) -> dict[str, Any]:
    safe = {"revenue_poc.tool.name", "revenue_poc.step.id", "revenue_poc.plan.version", "revenue_poc.evidence.count", "revenue_poc.replan.count", "revenue_poc.stop.reason", "revenue_poc.semantic.requirement_id", "revenue_poc.runtime.mode", "args_fingerprint"}
    redacted = redact_mapping(attributes, capture_content=config.capture_content, limit=config.max_attribute_length)
    for key, value in attributes.items():
        if key in safe and isinstance(value, (str, int, float, bool)) and not str(value).startswith("/"):
            redacted[key] = str(value)[:config.max_attribute_length] if isinstance(value, str) else value
    return redacted

def _duration(start: str, finish: str) -> float:
    from datetime import datetime
    return max(0.0, (datetime.fromisoformat(finish.replace("Z", "+00:00")) - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds() * 1000)


def get_recorder() -> TraceRecorder: return TraceRecorder()
