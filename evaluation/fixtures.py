from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analysis_pipeline import PipelineContext
from analyzer import AnalysisArtifacts
from mapping_parser import ParsedMapping
from utils import MessageCollector

_ALLOWED_FIXTURES = {
    "proactive-new-scan-v1",
    "proactive-unchanged-v1",
    "proactive-quality-blocker-v1",
    "proactive-divergence-v1",
}


@dataclass(frozen=True)
class ProactiveFixture:
    fixture_id: str
    context: PipelineContext
    assistant_factory: object


class DeterministicProactiveAssistant:
    def __init__(self, request_id: str) -> None:
        self.request_id = request_id

    def answer(self, question: str) -> dict:
        return {
            "summary": "Synthetic proactive investigation completed.",
            "answer_contract": {
                "status": "completed",
                "limitations": [
                    "僅描述歷史資料，不做 forecast 或 root cause 判定。",
                    "目前工具或資料無法執行反向證據搜尋；這不代表沒有反證。",
                ],
            },
            "domain_results": [
                {
                    "domain": "financial",
                    "status": "completed",
                    "used_tools": ["get_revenue_inventory_relationship"],
                    "key_findings": ["paired revenue/inventory evidence"],
                }
            ],
            "agent_runtime": {"status": "completed", "stop_reason": "completed"},
        }


def build_proactive_fixture(fixture_id: str) -> ProactiveFixture:
    if fixture_id not in _ALLOWED_FIXTURES:
        raise ValueError(f"unsupported_proactive_fixture:{fixture_id}")
    quality_blocker = fixture_id == "proactive-quality-blocker-v1"
    context = _build_context(quality_blocker=quality_blocker)
    return ProactiveFixture(fixture_id=fixture_id, context=context, assistant_factory=lambda request_id: DeterministicProactiveAssistant(request_id))


def build_mcp_fixture(fixture_id: str) -> ProactiveFixture:
    # Evaluation-only fixture entrypoint. IDs are allowlisted and never interpreted as paths, modules, or serialized code.
    if fixture_id == "mcp-basic-v1":
        context = _build_context(quality_blocker=False)
    elif fixture_id == "mcp-row-cap-v1":
        context = _build_many_group_context(30)
    else:
        raise ValueError(f"unsupported_mcp_fixture:{fixture_id}")
    return ProactiveFixture(fixture_id=fixture_id, context=context, assistant_factory=lambda request_id: DeterministicProactiveAssistant(request_id))


def _build_context(*, quality_blocker: bool) -> PipelineContext:
    revenue_df = pd.DataFrame(
        {
            "month_key": ["2025-01", "2025-02", "2025-03"],
            "month": ["2025-01", "2025-02", "2025-03"],
            "revenue": [120.0, 100.0, 80.0],
            "revenue_amount": [120.0, 100.0, 80.0],
            "business_group": ["Alpha", "Alpha", "Alpha"],
            "product_line_5": ["LineA", "LineA", "LineA"],
            "platform": ["Alpha", "Alpha", "Alpha"],
        }
    )
    inventory_df = pd.DataFrame(
        {
            "month_key": ["2025-01", "2025-02", "2025-03"],
            "month": ["2025-01", "2025-02", "2025-03"],
            "inventory_amount": [50.0, 60.0, 75.0],
            "inventory_qty": [5.0, 6.0, 7.0],
            "business_group": ["Alpha", "Alpha", "Alpha"],
            "product_line_5": ["LineA", "LineA", "LineA"],
            "platform": ["Alpha", "Alpha", "Alpha"],
        }
    )
    if quality_blocker:
        inventory_df = inventory_df.drop(columns=["inventory_amount"])
    aligned = _aligned_frame()
    artifacts = _artifacts(aligned)
    return PipelineContext(
        inventory_check={"missing": [], "extra": []},
        revenue_check={"missing": [], "extra": []},
        inventory_df=inventory_df,
        revenue_df=revenue_df,
        parsed_mapping=_parsed_mapping(),
        artifacts=artifacts,
        messages=MessageCollector(),
        supported_domains={"sales": True, "inventory": not quality_blocker, "financial": True, "association": False, "chart": True},
        source_files={"inventory": "synthetic-fixture", "revenue": "synthetic-fixture", "mapping": "synthetic-fixture"},
        real_data_quality_report=None,
    )


def _aligned_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "month_key": ["2025-01", "2025-02", "2025-03"],
            "business_group": ["Alpha", "Alpha", "Alpha"],
            "product_line_5": ["LineA", "LineA", "LineA"],
            "platform": ["Alpha", "Alpha", "Alpha"],
            "revenue_amount": [120.0, 100.0, 80.0],
            "inventory_amount": [50.0, 60.0, 75.0],
            "inventory_qty": [5.0, 6.0, 7.0],
            "data_presence_flag": ["both", "both", "both"],
        }
    )


def _artifacts(aligned: pd.DataFrame) -> AnalysisArtifacts:
    monthly_revenue = aligned.groupby("month_key", as_index=False)["revenue_amount"].sum().rename(columns={"month_key": "月份", "revenue_amount": "營收"})
    monthly_inventory_amount = aligned.groupby("month_key", as_index=False)["inventory_amount"].sum().rename(columns={"month_key": "月份", "inventory_amount": "金額"})
    monthly_inventory_qty = aligned.groupby("month_key", as_index=False)["inventory_qty"].sum().rename(columns={"month_key": "月份", "inventory_qty": "QTY"})
    empty = pd.DataFrame()
    return AnalysisArtifacts(
        inventory_enriched=empty,
        revenue_enriched=empty,
        monthly_revenue=monthly_revenue,
        monthly_inventory_amount=monthly_inventory_amount,
        monthly_inventory_qty=monthly_inventory_qty,
        revenue_by_group=empty,
        inventory_by_group=empty,
        merged_analysis=empty,
        platform_monthly_analysis=empty,
        anomalies=empty,
        correlation_analysis=empty,
        summary_metrics={
            "monthly_revenue": monthly_revenue,
            "monthly_inventory_amount": monthly_inventory_amount,
            "monthly_inventory_qty": monthly_inventory_qty,
        },
        report_context={},
        inventory_monthly_entity=aligned,
        revenue_monthly_entity=aligned,
        revenue_inventory_aligned=aligned,
        data_quality_report={},
    )


def _parsed_mapping() -> ParsedMapping:
    mapping = pd.DataFrame({"事業群代碼": ["Alpha"], "事業群名稱": ["Alpha"]})
    return ParsedMapping(
        raw_mapping=pd.DataFrame(),
        structured_mapping=mapping.copy(),
        business_group_mapping=mapping.copy(),
        inventory_hqbu_mapping=pd.DataFrame(),
        revenue_platform_mapping=pd.DataFrame(),
        anonymization_rules=pd.DataFrame(),
        bridge_candidates=pd.DataFrame(),
        mapping_success=True,
        warnings=[],
    )


def _build_many_group_context(group_count: int) -> PipelineContext:
    groups = [f"Group{i:02d}" for i in range(1, group_count + 1)]
    months = ["2025-01", "2025-02", "2025-03"]
    rows = []
    for group_index, group in enumerate(groups, start=1):
        for month_index, month in enumerate(months, start=1):
            rows.append(
                {
                    "month_key": month,
                    "month": month,
                    "business_group": group,
                    "product_line_5": "LineA",
                    "platform": group,
                    "revenue_amount": float(1000 + group_index * 10 - month_index),
                    "inventory_amount": float(100 + group_index + month_index),
                    "inventory_qty": float(10 + group_index + month_index),
                    "data_presence_flag": "both",
                }
            )
    aligned = pd.DataFrame(rows)
    revenue_df = aligned[["month_key", "month", "revenue_amount", "business_group", "product_line_5", "platform"]].copy()
    revenue_df["revenue"] = revenue_df["revenue_amount"]
    inventory_df = aligned[["month_key", "month", "inventory_amount", "inventory_qty", "business_group", "product_line_5", "platform"]].copy()
    artifacts = _artifacts(aligned)
    mapping = pd.DataFrame({"事業群代碼": groups, "事業群名稱": groups})
    parsed = ParsedMapping(
        raw_mapping=pd.DataFrame(),
        structured_mapping=mapping.copy(),
        business_group_mapping=mapping.copy(),
        inventory_hqbu_mapping=pd.DataFrame(),
        revenue_platform_mapping=pd.DataFrame(),
        anonymization_rules=pd.DataFrame(),
        bridge_candidates=pd.DataFrame(),
        mapping_success=True,
        warnings=[],
    )
    return PipelineContext(
        inventory_check={"missing": [], "extra": []},
        revenue_check={"missing": [], "extra": []},
        inventory_df=inventory_df,
        revenue_df=revenue_df,
        parsed_mapping=parsed,
        artifacts=artifacts,
        messages=MessageCollector(),
        supported_domains={"sales": True, "inventory": True, "financial": True, "association": False, "chart": True},
        source_files={"inventory": "synthetic-fixture", "revenue": "synthetic-fixture", "mapping": "synthetic-fixture"},
        real_data_quality_report=None,
    )
