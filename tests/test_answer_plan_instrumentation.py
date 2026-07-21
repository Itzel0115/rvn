from observability.config import ObservabilityConfig
from observability.store import SQLiteTraceStore
from observability.tracing import TraceRecorder
from answer_plan import AnswerPlan
from semantic_layer.adapters import enrich_answer_plan

class _Task: task_family="metric_relationship_analysis"
def test_semantic_answer_plan_enrichment_emits_span(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSERVABILITY_ENABLED", "true"); monkeypatch.setenv("TRACE_STORE_PATH", str(tmp_path/"t.sqlite3"))
    store=SQLiteTraceStore(tmp_path/"t.sqlite3"); recorder=TraceRecorder(ObservabilityConfig(enabled=True,database_path=tmp_path/"t.sqlite3"),store)
    with recorder.run("agent.request",request_id="plan-span"): enrich_answer_plan(AnswerPlan(),_Task())
    assert "semantic.answer_plan.enrich" in [s["span_name"] for s in store.get_trace("plan-span")["spans"]]
