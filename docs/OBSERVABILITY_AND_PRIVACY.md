# Observability and Privacy

Tracing is local-first and disabled by default (`OBSERVABILITY_ENABLED=false`). When enabled, the SQLite store is `output/observability/traces.sqlite3`; no OTLP endpoint or SaaS exporter is configured.

The project uses `opentelemetry-api` and `opentelemetry-sdk` 1.43 as an API/SDK dependency. `SQLiteSpanExporter` is a local best-effort exporter, not a claim of full OpenTelemetry GenAI convention compliance. Project fields use the `revenue_poc.*` namespace. Stable trace concepts (trace/span/status) are used; GenAI attributes are not asserted because the application has no reliable per-call usage metadata.

Content capture is off by default. With `TRACE_CAPTURE_CONTENT=true`, values are redacted and truncated; raw DataFrames, source rows, prompts, completions, secrets, absolute paths, and Excel names remain prohibited. Sensitive keys including API keys, tokens, passwords, authorization headers, cookies, and connection strings are redacted. Non-finite numbers, control characters, log injection, nesting, and long strings are sanitized.

Retention is only available through `observability.cli purge --older-than-days N --confirm` and only deletes trace records, never AgentRunState, proactive state, approvals, or publications.
