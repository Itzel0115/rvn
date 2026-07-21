from __future__ import annotations

from opentelemetry.sdk.trace.export import SpanExportResult, SpanExporter

from .models import SpanRecord
from .store import SQLiteTraceStore


class SQLiteSpanExporter(SpanExporter):
    """Best-effort local exporter; no OTLP and no failure propagation."""
    def __init__(self, store: SQLiteTraceStore) -> None: self.store = store
    def export(self, spans):  # type: ignore[no-untyped-def]
        try:
            for source in spans:
                context = source.get_span_context(); parent = source.parent.span_id if source.parent else None
                self.store.save_span(SpanRecord(trace_id=f"{context.trace_id:032x}", span_id=f"{context.span_id:016x}", parent_span_id=f"{parent:016x}" if parent else None, span_name=source.name, status="ok" if source.status.is_ok else "error", attributes=dict(source.attributes or {})))
            return SpanExportResult.SUCCESS
        except Exception:
            return SpanExportResult.FAILURE
    def shutdown(self) -> None: return None
