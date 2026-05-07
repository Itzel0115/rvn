from __future__ import annotations

from analysis_pipeline import build_pipeline_context
from multi_agent import MultiAgentAssistant
from ollama_client import OllamaCallResult


class StubLLM:
    def generate(self, **kwargs):
        return OllamaCallResult(ok=False, text="", data=None, error="stub")

    def generate_json(self, **kwargs):
        return OllamaCallResult(ok=False, text="", data=None, error="stub")


_CONTEXT = None


def get_context():
    global _CONTEXT
    if _CONTEXT is None:
        _CONTEXT = build_pipeline_context("test-suite")
    return _CONTEXT


def build_stubbed_assistant(
    request_id: str = "test-suite",
    *,
    use_llm_planner: bool | None = None,
    use_llm_rewriter: bool | None = None,
    llm_client: StubLLM | None = None,
) -> MultiAgentAssistant:
    assistant = MultiAgentAssistant(
        get_context(),
        request_id,
        use_llm_planner=use_llm_planner,
        use_llm_rewriter=use_llm_rewriter,
    )
    stub = llm_client or StubLLM()
    assistant.llm_client = stub
    for agent in assistant.agents.values():
        agent.llm_client = stub
    return assistant
