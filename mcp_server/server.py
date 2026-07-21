from __future__ import annotations

import json
import os
import sys
from contextlib import redirect_stdout
from typing import Any

from mcp.server.fastmcp import FastMCP

from analysis_pipeline import build_pipeline_context
from analysis_tools import AnalysisToolbox
from logging_utils import build_request_id
from observability import get_recorder
from tool_registry import TOOL_REGISTRY
from .resources import read_resource
from .security import enforce_row_limit, validate_tool_arguments

mcp = FastMCP("revenue-inventory-analytics")
_toolbox: AnalysisToolbox | None = None

def _get_toolbox() -> AnalysisToolbox:
    global _toolbox
    if _toolbox is None:
        request_id = build_request_id("mcp")
        fixture_id = os.getenv("REVENUE_POC_EVAL_FIXTURE_ID")
        if fixture_id:
            # Evaluation-only fixture mode. The fixture ID is allowlisted in evaluation.fixtures; it is not a path or import string.
            from evaluation.fixtures import build_mcp_fixture
            context = build_mcp_fixture(fixture_id).context
        else:
            context = build_pipeline_context(request_id)
        _toolbox = AnalysisToolbox(context, request_id)
    return _toolbox

def _call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    recorder = get_recorder()
    with recorder.run("mcp.server.request", request_id=build_request_id("mcp"), runtime_mode="mcp") as trace:
      try:
        with recorder.span("mcp.security.validate", attributes={"revenue_poc.tool.name": tool_name, "argument_count": len(arguments)}):
            args = validate_tool_arguments(tool_name, arguments)
        with recorder.span("mcp.tool.call", attributes={"revenue_poc.tool.name": tool_name}):
            with redirect_stdout(sys.stderr):
                toolbox = _get_toolbox()
                output = getattr(toolbox, tool_name)(**args)
            result = {"tool_name": tool_name, "evidence_type": output.get("evidence_type") if isinstance(output, dict) and output.get("evidence_type") else TOOL_REGISTRY[tool_name].output_evidence_type, "result": enforce_row_limit(output)}
        recorder.finish_run(trace, status="completed", counters={"tool_call_count": 1})
        return result
      except (ValueError, KeyError, TypeError, RuntimeError, OSError) as exc:
        recorder.finish_run(trace, status="partial", failure_category="mcp_policy_rejection", counters={"tool_call_count": 1})
        raise ValueError(f"mcp_tool_rejected:{type(exc).__name__}") from None

@mcp.tool(name="get_entity_month_table")
def get_entity_month_table(entity_dimension: str, metric: str, month: str, parent_filter: dict[str, Any] | None = None, include_qty: bool = True) -> dict[str, Any]:
    """Read-only entity rows for an explicit month; result is capped and sanitized."""
    return _call("get_entity_month_table", {"entity_dimension": entity_dimension, "metric": metric, "month": month, "parent_filter": parent_filter, "include_qty": include_qty})

@mcp.tool(name="get_entity_metric_ranking")
def get_entity_metric_ranking(entity_dimension: str, metric: str, month: str | None = None, top_n: int = 5, parent_filter: dict[str, Any] | None = None, sort_direction: str | None = None) -> dict[str, Any]:
    return _call("get_entity_metric_ranking", {"entity_dimension": entity_dimension, "metric": metric, "month": month, "top_n": top_n, "parent_filter": parent_filter, "sort_direction": sort_direction})

@mcp.tool(name="get_entity_performance_snapshot")
def get_entity_performance_snapshot(entity_dimension: str, month: str | None = None, parent_filter: dict[str, Any] | None = None, top_n: int | None = None) -> dict[str, Any]:
    """Supporting scorecard context; it is not relationship primary evidence."""
    return _call("get_entity_performance_snapshot", {"entity_dimension": entity_dimension, "month": month, "parent_filter": parent_filter, "top_n": top_n})

@mcp.tool(name="get_overall_time_series")
def get_overall_time_series(metric: str, recent_n: int | None = None, start_month: str | None = None, end_month: str | None = None) -> dict[str, Any]:
    return _call("get_overall_time_series", {"metric": metric, "recent_n": recent_n, "start_month": start_month, "end_month": end_month})

@mcp.tool(name="get_revenue_inventory_relationship")
def get_revenue_inventory_relationship(entity_dimension: str, recent_n: int | None = None, month: str | None = None, parent_filter: dict[str, Any] | None = None) -> dict[str, Any]:
    return _call("get_revenue_inventory_relationship", {"entity_dimension": entity_dimension, "recent_n": recent_n, "month": month, "parent_filter": parent_filter})

@mcp.tool(name="get_data_coverage")
def get_data_coverage() -> dict[str, Any]:
    return _call("get_data_coverage", {})

def _resource(uri: str) -> str:
    recorder = get_recorder()
    with recorder.run("mcp.server.request", request_id=build_request_id("mcp-resource"), runtime_mode="mcp") as trace:
        try:
            with recorder.span("mcp.resource.read", attributes={"resource_uri_hash": str(abs(hash(uri)))[:16]}):
                payload = json.dumps(read_resource(uri), ensure_ascii=False)
            recorder.finish_run(trace, status="completed")
            return payload
        except KeyError:
            recorder.finish_run(trace, status="partial", failure_category="mcp_policy_rejection")
            raise ValueError("resource_not_found") from None

@mcp.resource("semantic://catalog/summary")
def catalog_summary() -> str: return _resource("semantic://catalog/summary")
@mcp.resource("semantic://metrics")
def metrics() -> str: return _resource("semantic://metrics")
@mcp.resource("semantic://metrics/{metric_id}")
def metric(metric_id: str) -> str: return _resource(f"semantic://metrics/{metric_id}")
@mcp.resource("semantic://dimensions")
def dimensions() -> str: return _resource("semantic://dimensions")
@mcp.resource("semantic://dimensions/{dimension_id}")
def dimension(dimension_id: str) -> str: return _resource(f"semantic://dimensions/{dimension_id}")
@mcp.resource("semantic://tasks/{task_type}")
def task(task_type: str) -> str: return _resource(f"semantic://tasks/{task_type}")
@mcp.resource("semantic://tools")
def tools_resource() -> str: return _resource("semantic://tools")
@mcp.resource("semantic://data-contracts")
def data_contracts() -> str: return _resource("semantic://data-contracts")
@mcp.resource("semantic://data-freshness")
def data_freshness() -> str: return _resource("semantic://data-freshness")

def main() -> None: mcp.run(transport="stdio")
if __name__ == "__main__": main()
