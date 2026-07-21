from agent_runtime.models import AgentRunState,PlanStep
from agent_runtime.runtime import StatefulAgentRuntime
from agent_runtime.state_store import InMemoryAgentStateStore
from observability.config import ObservabilityConfig
from observability.store import SQLiteTraceStore
from observability.tracing import TraceRecorder

def test_disabled_recorder_does_not_change_runtime():
    state=AgentRunState(request_id="r",thread_id="r",question="q",canonical_task={},steps=[PlanStep("p1",1,1,"tool")])
    result=StatefulAgentRuntime(executor=lambda *_:{"rows":[{"metric":"x"}]} ,state_store=InMemoryAgentStateStore()).run(state)
    assert result.status.value=="completed"

def test_enabled_recorder_parent_child_store(tmp_path):
    recorder=TraceRecorder(ObservabilityConfig(enabled=True,database_path=tmp_path/"trace.sqlite3"),SQLiteTraceStore(tmp_path/"trace.sqlite3"))
    with recorder.run("agent.run",request_id="req") as trace:
        with recorder.span("tool.execute",attributes={"tool_name":"get_entity_month_table"}): pass
    saved=recorder.store.get_trace("req")
    assert saved and len(saved["spans"])==2 and saved["spans"][1]["parent_span_id"]==trace.root_span_id
