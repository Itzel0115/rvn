"""正式資料 Pipeline 的組裝入口。

本模組集中載入 `data/inventory.xlsx` 與 `data/revenue.xlsx`，呼叫
`real_data.py` 完成 normalization、entity/month alignment，並建立 API、
Agent 與 analysis tools 共用的 `PipelineContext`。正式資料驗證失敗時直接
回報 inventory/revenue 問題，不再 fallback 到 mapping workbook；
`ParsedMapping` 只承載由正式資料衍生的 compatibility metadata。
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from analyzer import AnalysisArtifacts
from config import CHART_DIR, COL_GROUP_CODE, COL_GROUP_NAME, DATA_DIR, INVENTORY_FILE, OUTPUT_DIR, REVENUE_FILE
from data_loader import load_real_data_sources
from logging_utils import get_logger
from mapping_parser import ParsedMapping
from real_data import build_legacy_compatible_frames, build_real_analysis_tables
from utils import MessageCollector, ensure_directories


@dataclass
class PipelineContext:
    """供 Backend、Agent 與所有 Tool 共用的正規化資料與分析 artifacts。"""
    inventory_check: dict[str, list[str]]
    revenue_check: dict[str, list[str]]
    inventory_df: pd.DataFrame
    revenue_df: pd.DataFrame
    parsed_mapping: ParsedMapping
    artifacts: AnalysisArtifacts
    messages: MessageCollector
    supported_domains: dict[str, bool]
    source_files: dict[str, str]
    real_data_quality_report: dict | None = None


def build_pipeline_context(request_id: str) -> PipelineContext:
    """建立共用分析上下文；資料驗證失敗時直接回報 inventory/revenue 錯誤。"""
    logger = get_logger("analysis_pipeline", request_id, domain="pipeline")
    ensure_directories([DATA_DIR, OUTPUT_DIR, CHART_DIR])

    logger.info("Loading source files")
    logger.info("Using inventory file: %s", INVENTORY_FILE)
    logger.info("Using revenue file: %s", REVENUE_FILE)
    messages = MessageCollector()
    real_inventory_df, real_revenue_df, real_source_metadata = load_real_data_sources(INVENTORY_FILE, REVENUE_FILE, messages)
    if not real_inventory_df.empty and not real_revenue_df.empty:
        # 兩份來源在此統一完成對齊，避免不同 Tool 各自定義月份或 entity grain。
        logger.info("Loaded real data files by configured file path; building Phase 9A entity analysis tables")
        real_tables = build_real_analysis_tables(real_inventory_df, real_revenue_df, real_source_metadata)
        for message in real_tables.messages:
            messages.add_warning(message)

        frames = build_legacy_compatible_frames(real_tables)
        business_groups = sorted(
            set(real_inventory_df["business_group"].dropna().astype(str).tolist())
            | set(real_revenue_df["business_group"].dropna().astype(str).tolist())
        )
        business_group_mapping = pd.DataFrame(
            [{COL_GROUP_CODE: group, COL_GROUP_NAME: group} for group in business_groups]
        )
        parsed_mapping = ParsedMapping(
            raw_mapping=pd.DataFrame(),
            structured_mapping=business_group_mapping.copy(),
            business_group_mapping=business_group_mapping,
            inventory_hqbu_mapping=pd.DataFrame(),
            revenue_platform_mapping=pd.DataFrame(),
            anonymization_rules=pd.DataFrame(),
            bridge_candidates=pd.DataFrame(),
            mapping_success=True,
            warnings=real_tables.messages,
        )

        summary_metrics = {
            "monthly_revenue": frames["monthly_revenue"],
            "monthly_inventory_amount": frames["monthly_inventory_amount"],
            "monthly_inventory_qty": frames["monthly_inventory_qty"],
            "revenue_by_group": frames["revenue_by_group"],
            "inventory_by_group": frames["inventory_by_group"],
            "anomalies": frames["anomalies"],
            "correlation_analysis": frames["correlation_analysis"],
            "inventory_monthly_entity": real_tables.inventory_monthly_entity,
            "revenue_monthly_entity": real_tables.revenue_monthly_entity,
            "revenue_inventory_aligned": real_tables.revenue_inventory_aligned,
        }
        artifacts = AnalysisArtifacts(
            inventory_enriched=frames["inventory_enriched"],
            revenue_enriched=frames["revenue_enriched"],
            monthly_revenue=frames["monthly_revenue"],
            monthly_inventory_amount=frames["monthly_inventory_amount"],
            monthly_inventory_qty=frames["monthly_inventory_qty"],
            revenue_by_group=frames["revenue_by_group"],
            inventory_by_group=frames["inventory_by_group"],
            merged_analysis=frames["merged_analysis"],
            platform_monthly_analysis=frames["platform_monthly_analysis"],
            anomalies=frames["anomalies"],
            correlation_analysis=frames["correlation_analysis"],
            summary_metrics=summary_metrics,
            report_context={
                **real_tables.data_quality_report,
                "real_data": True,
                "monthly_revenue_records": frames["monthly_revenue"].to_dict(orient="records"),
                "monthly_inventory_amount_records": frames["monthly_inventory_amount"].to_dict(orient="records"),
                "monthly_inventory_qty_records": frames["monthly_inventory_qty"].to_dict(orient="records"),
                "revenue_by_group_records": frames["revenue_by_group"].to_dict(orient="records"),
                "inventory_by_group_records": frames["inventory_by_group"].to_dict(orient="records"),
                "platform_analysis_records": frames["platform_monthly_analysis"].head(20).to_dict(orient="records"),
                "merged_analysis_available": not frames["merged_analysis"].empty,
            },
            inventory_monthly_entity=real_tables.inventory_monthly_entity,
            revenue_monthly_entity=real_tables.revenue_monthly_entity,
            revenue_inventory_aligned=real_tables.revenue_inventory_aligned,
            data_quality_report=real_tables.data_quality_report,
        )
        inventory_check = {"missing": [], "extra": []}
        revenue_check = {"missing": [], "extra": []}
        supported_domains = {
            "sales": not artifacts.monthly_revenue.empty,
            "inventory": not artifacts.monthly_inventory_amount.empty,
            "financial": not artifacts.revenue_inventory_aligned.empty,
            "association": False,
            "chart": not artifacts.revenue_inventory_aligned.empty,
        }
        logger.info(
            "Real analysis complete: inventory_entity=%s revenue_entity=%s aligned=%s",
            len(real_tables.inventory_monthly_entity),
            len(real_tables.revenue_monthly_entity),
            len(real_tables.revenue_inventory_aligned),
        )
        return PipelineContext(
            inventory_check=inventory_check,
            revenue_check=revenue_check,
            inventory_df=real_inventory_df,
            revenue_df=real_revenue_df,
            parsed_mapping=parsed_mapping,
            artifacts=artifacts,
            messages=messages,
            supported_domains=supported_domains,
            source_files={
                "inventory": str(INVENTORY_FILE),
                "revenue": str(REVENUE_FILE),
            },
            real_data_quality_report=real_tables.data_quality_report,
        )

    inventory_status = "loaded" if not real_inventory_df.empty else "missing or invalid"
    revenue_status = "loaded" if not real_revenue_df.empty else "missing or invalid"
    validation_details = "; ".join(messages.errors) or "normalization produced no usable rows"
    raise ValueError(
        "Real-data validation failed: "
        f"inventory source={INVENTORY_FILE} ({inventory_status}); "
        f"revenue source={REVENUE_FILE} ({revenue_status}); "
        f"details={validation_details}"
    )
