"""共用 deterministic analysis tools。

`AnalysisToolbox` 只使用 PipelineContext 內已正規化的 inventory/revenue，
避免各 Tool 重複讀檔或產生不同口徑。公開結果以 records、限制與 evidence
欄位為主，供 Agent validator、API 與 frontend 使用；Tool 名稱和 output
schema 需與 registry 保持相容。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numbers

import pandas as pd

from analysis_pipeline import PipelineContext
from config import (
    CHART_DIR,
    COL_ANOMALY_REASON,
    COL_ANOMALY_SIGNAL,
    COL_ANOMALY_TYPE,
    COL_CORR_LABEL,
    COL_CORR_LEVEL,
    COL_CORR_METRICS,
    COL_CORR_SAMPLES,
    COL_CORR_TARGET,
    COL_CORR_VALUE,
    COL_GROUP_CODE,
    COL_GROUP_NAME,
    COL_INV_AMOUNT,
    COL_INV_QTY,
    COL_MONTH,
    COL_PLATFORM,
    COL_REVENUE,
    COL_REVENUE_INV_AMOUNT_RATIO,
    COL_REVENUE_INV_QTY_RATIO,
)
from logging_utils import get_logger
from utils import format_number
from visualizer import render_chart_payload
from entity_labels import ENTITY_DISPLAY_LABELS, display_label_for_dimension, normalize_entity_dimension, resolve_entity_value


@dataclass
class QueryFilters:
    month: str | None = None
    platform: str | None = None
    group_code: str | None = None


ENTITY_LABELS = ENTITY_DISPLAY_LABELS

UNMAPPED_ENTITY_VALUES = {"", "未對應", "未分類", "unknown", "n/a", "nan", "none", "null"}


def is_unmapped_entity(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text.lower() in UNMAPPED_ENTITY_VALUES


def _normalize_observation_filter_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"all", "none", "null"} or text in {"全部", "全部事業群", "全部產品線"}:
        return None
    return text


@dataclass
class ObservationRequest:
    row_dimension: str = "business_group"
    metric: str = "revenue"
    compare_mode: str = "previous_period"
    current_month: str | None = None
    compare_month: str | None = None
    platform: str | None = None
    group_code: str | None = None
    product_line_5: str | None = None
    product_line: str | None = None

    def __post_init__(self) -> None:
        if self.row_dimension == "product_line":
            self.row_dimension = "product_line_5"
        self.platform = _normalize_observation_filter_value(self.platform)
        self.group_code = _normalize_observation_filter_value(self.group_code)
        self.product_line_5 = _normalize_observation_filter_value(self.product_line_5 or self.product_line)
        self.product_line = self.product_line_5


class AnalysisToolbox:
    """Tool layer that wraps the existing analysis artifacts without rewriting them."""

    _CHART_DEFINITIONS = {
        "business_group_revenue_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各事業群營收比較",
            "x_label": "事業群",
            "y_label": "營收",
            "label_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
            "series_name": "營收",
            "default_latest_month": True,
        },
        "business_group_inventory_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各事業群庫存金額比較",
            "x_label": "事業群",
            "y_label": "庫存金額",
            "label_column": COL_PLATFORM,
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
            "default_latest_month": True,
        },
        "business_group_revenue_pie": {
            "metric": "platform_monthly",
            "chart_type": "pie",
            "title": "最新月份各事業群營收圓餅圖",
            "x_label": "事業群",
            "y_label": "營收",
            "label_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
            "series_name": "營收",
            "default_latest_month": True,
        },
        "business_group_inventory_pie": {
            "metric": "platform_monthly",
            "chart_type": "pie",
            "title": "最新月份各事業群庫存金額圓餅圖",
            "x_label": "事業群",
            "y_label": "庫存金額",
            "label_column": COL_PLATFORM,
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
            "default_latest_month": True,
        },
        "business_group_health_score_bar": {
            "metric": "entity_health_score",
            "chart_type": "bar",
            "title": "事業群 health_score 排名",
            "x_label": "事業群",
            "y_label": "health_score",
            "label_column": "entity_value",
            "value_column": "health_score",
            "series_name": "health_score",
            "entity_dimension": "business_group",
        },
        "business_group_revenue_inventory_ratio_bar": {
            "metric": "entity_health_score",
            "chart_type": "bar",
            "title": "事業群營收/庫存金額 proxy 排名",
            "x_label": "事業群",
            "y_label": "營收/庫存金額 proxy",
            "label_column": "entity_value",
            "value_column": "revenue_inventory_amount_ratio",
            "series_name": "營收/庫存金額 proxy",
            "entity_dimension": "business_group",
            "sort_ascending": True,
        },
        "product_line_revenue_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各產品線營收比較",
            "x_label": "產品線",
            "y_label": "營收",
            "label_column": "product_line_5",
            "value_column": COL_REVENUE,
            "series_name": "營收",
            "default_latest_month": True,
        },
        "product_line_inventory_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各產品線庫存金額比較",
            "x_label": "產品線",
            "y_label": "庫存金額",
            "label_column": "product_line_5",
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
            "default_latest_month": True,
        },
        "product_line_revenue_pie": {
            "metric": "platform_monthly",
            "chart_type": "pie",
            "title": "最新月份各產品線營收圓餅圖",
            "x_label": "產品線",
            "y_label": "營收",
            "label_column": "product_line_5",
            "value_column": COL_REVENUE,
            "series_name": "營收",
            "default_latest_month": True,
        },
        "product_line_inventory_pie": {
            "metric": "platform_monthly",
            "chart_type": "pie",
            "title": "最新月份各產品線庫存金額圓餅圖",
            "x_label": "產品線",
            "y_label": "庫存金額",
            "label_column": "product_line_5",
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
            "default_latest_month": True,
        },
        "product_line_health_score_bar": {
            "metric": "entity_health_score",
            "chart_type": "bar",
            "title": "產品線 health_score 排名",
            "x_label": "產品線",
            "y_label": "health_score",
            "label_column": "entity_value",
            "value_column": "health_score",
            "series_name": "health_score",
            "entity_dimension": "product_line_5",
        },
        "product_line_revenue_inventory_ratio_bar": {
            "metric": "entity_health_score",
            "chart_type": "bar",
            "title": "產品線營收/庫存金額 proxy 排名",
            "x_label": "產品線",
            "y_label": "營收/庫存金額 proxy",
            "label_column": "entity_value",
            "value_column": "revenue_inventory_amount_ratio",
            "series_name": "營收/庫存金額 proxy",
            "entity_dimension": "product_line_5",
            "sort_ascending": True,
        },
        "current_month_business_group_revenue_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各事業群營收比較",
            "x_label": "事業群",
            "y_label": "營收",
            "label_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
            "series_name": "營收",
            "default_latest_month": True,
        },
        "current_month_business_group_inventory_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各事業群庫存金額比較",
            "x_label": "事業群",
            "y_label": "庫存金額",
            "label_column": COL_PLATFORM,
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
            "default_latest_month": True,
        },
        "business_group_ratio_rank": {
            "metric": "entity_health_score",
            "chart_type": "bar",
            "title": "事業群營收/庫存金額 proxy 排名（由弱到強）",
            "x_label": "事業群",
            "y_label": "營收/庫存金額 proxy",
            "label_column": "entity_value",
            "value_column": "revenue_inventory_amount_ratio",
            "series_name": "營收/庫存金額 proxy",
            "entity_dimension": "business_group",
            "sort_ascending": True,
        },
        "business_group_revenue_inventory": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "事業群營收比較",
            "x_label": "事業群",
            "y_label": "營收",
            "label_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
            "series_name": "營收",
        },
        "product_line_revenue_inventory": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "產品線營收比較",
            "x_label": "產品線",
            "y_label": "營收",
            "label_column": "product_line_5",
            "value_column": COL_REVENUE,
            "series_name": "營收",
        },
        "business_group_health_score": {
            "metric": "entity_health_score",
            "chart_type": "bar",
            "title": "事業群 health_score 排名",
            "x_label": "事業群",
            "y_label": "health_score",
            "label_column": "entity_value",
            "value_column": "health_score",
            "series_name": "health_score",
            "entity_dimension": "business_group",
        },
        "product_line_health_score": {
            "metric": "entity_health_score",
            "chart_type": "bar",
            "title": "產品線 health_score 排名",
            "x_label": "產品線",
            "y_label": "health_score",
            "label_column": "entity_value",
            "value_column": "health_score",
            "series_name": "health_score",
            "entity_dimension": "product_line_5",
        },
        "overall_revenue_trend_line": {
            "metric": "revenue_monthly",
            "chart_type": "line",
            "title": "總體營收趨勢",
            "x_label": "月份",
            "y_label": "營收",
            "value_column": COL_REVENUE,
            "series_name": "總營收",
        },
        "monthly_revenue_trend": {
            "metric": "revenue_monthly",
            "chart_type": "line",
            "title": "各月份總營收趨勢",
            "x_label": "月份",
            "y_label": "營收",
            "value_column": COL_REVENUE,
            "series_name": "總營收",
        },
        "monthly_inventory_amount_trend": {
            "metric": "inventory_amount_monthly",
            "chart_type": "line",
            "title": "各月份總庫存金額趨勢",
            "x_label": "月份",
            "y_label": "庫存金額",
            "value_column": COL_INV_AMOUNT,
            "series_name": "總庫存金額",
        },
        "monthly_inventory_qty_trend": {
            "metric": "inventory_qty_monthly",
            "chart_type": "line",
            "title": "各月份總庫存QTY趨勢",
            "x_label": "月份",
            "y_label": "庫存QTY",
            "value_column": COL_INV_QTY,
            "series_name": "總庫存QTY",
        },
        "revenue_by_group_bar": {
            "metric": "revenue_by_group",
            "chart_type": "bar",
            "title": "各事業群營收分布",
            "x_label": "事業群",
            "y_label": "營收",
            "label_column": "事業群名稱",
            "value_column": COL_REVENUE,
            "series_name": "營收",
        },
        "inventory_by_group_bar": {
            "metric": "inventory_by_group",
            "chart_type": "bar",
            "title": "各事業群庫存金額分布",
            "x_label": "事業群",
            "y_label": "庫存金額",
            "label_column": "事業群名稱",
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
        },
        "entity_time_series_line": {
            "metric": "platform_monthly",
            "chart_type": "line",
            "title": "事業群各月營收趨勢",
            "x_label": "月份",
            "y_label": "營收",
            "label_column": COL_MONTH,
            "group_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
        },
        "platform_monthly_revenue": {
            "metric": "platform_monthly",
            "chart_type": "line",
            "title": "各事業群每月營收",
            "x_label": "月份",
            "y_label": "營收",
            "label_column": COL_MONTH,
            "group_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
        },
        "platform_monthly_inventory_amount": {
            "metric": "platform_monthly",
            "chart_type": "line",
            "title": "各事業群每月庫存金額",
            "x_label": "月份",
            "y_label": "庫存金額",
            "label_column": COL_MONTH,
            "group_column": COL_PLATFORM,
            "value_column": COL_INV_AMOUNT,
        },
        "platform_monthly_inventory_qty": {
            "metric": "platform_monthly",
            "chart_type": "line",
            "title": "各事業群每月庫存QTY",
            "x_label": "月份",
            "y_label": "庫存QTY",
            "label_column": COL_MONTH,
            "group_column": COL_PLATFORM,
            "value_column": COL_INV_QTY,
        },
        "platform_ratio_rank": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "事業群營收/庫存金額 proxy 排名（由弱到強）",
            "x_label": "月份 / 新事業群",
            "y_label": "營收/庫存金額比值",
            "label_column": "chart_label",
            "value_column": COL_REVENUE_INV_AMOUNT_RATIO,
            "series_name": "營收/庫存金額比值",
        },
        "current_month_platform_revenue_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各事業群營收比較",
            "x_label": "事業群",
            "y_label": "營收",
            "label_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
            "series_name": "營收",
            "default_latest_month": True,
        },
        "current_month_platform_inventory_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各事業群庫存金額比較",
            "x_label": "事業群",
            "y_label": "庫存金額",
            "label_column": COL_PLATFORM,
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
            "default_latest_month": True,
        },
        "anomaly_signal_rank": {
            "metric": "anomalies",
            "chart_type": "bar",
            "title": "異常訊號排行",
            "x_label": "月份 / 新事業群 / 類型",
            "y_label": "訊號強度",
            "label_column": "chart_label",
            "value_column": COL_ANOMALY_SIGNAL,
            "series_name": "訊號強度",
        },
    }

    _METRIC_FILTER_SUPPORT = {
        "revenue_trend": {"month", "platform", "group_code"},
        "inventory_amount_trend": {"month", "platform", "group_code"},
        "inventory_qty_trend": {"month", "platform", "group_code"},
        "revenue_monthly": {"month"},
        "inventory_amount_monthly": {"month"},
        "inventory_qty_monthly": {"month"},
        "revenue_by_group": {"group_code"},
        "inventory_by_group": {"group_code"},
        "platform_monthly": {"month", "platform", "group_code"},
        "entity_health_score": {"month", "platform", "group_code"},
        "anomalies": {"month", "platform", "group_code"},
        "correlations": set(),
    }

    def __init__(self, context: PipelineContext, request_id: str) -> None:
        self.context = context
        self.request_id = request_id

    def get_data_coverage(self) -> dict[str, Any]:
        """回傳來源、月份、列數與品質狀態，供 health/summary 使用。"""
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_data_coverage")

        months = self._collect_months()
        result = {
            "months": months,
            "inventory_rows": len(self.context.inventory_df),
            "revenue_rows": len(self.context.revenue_df),
            "mapping_rows": len(self.context.parsed_mapping.structured_mapping),
            "mapping_success": self.context.parsed_mapping.mapping_success,
            "supported_domains": self.context.supported_domains,
            "source_files": self.context.source_files,
            "real_data_quality_report": getattr(self.context.artifacts, "data_quality_report", {}) or getattr(self.context, "real_data_quality_report", {}),
        }
        logger.info("Completed tool get_data_coverage")
        return result

    def get_tool_capability_matrix(self) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_tool_capability_matrix")
        result = {
            "metrics": {
                metric: {
                    "supported_filters": sorted(supported_filters),
                    "available": self._metric_available(metric),
                }
                for metric, supported_filters in self._METRIC_FILTER_SUPPORT.items()
            },
            "tools": {
                "get_top_groups": {
                    "supported_filters": ["group_code", "platform"],
                    "available_metrics": ["revenue", "inventory"],
                },
                "get_platform_ranking": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available_metrics": ["revenue", "inventory_amount", "inventory_qty"],
                },
                "get_platform_ratios": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": not self.context.artifacts.platform_monthly_analysis.empty,
                    "warning": (
                        "Platform-aligned merged analysis is unavailable in the current dataset."
                        if self.context.artifacts.platform_monthly_analysis.empty
                        else None
                    ),
                },
                "get_entity_performance_snapshot": {
                    "supported_filters": ["month", "business_group", "product_line_5"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                    "description": "Deterministic entity scorecard using real-data business_group and product_line_5 grain.",
                },
                "get_entity_cross_section_comparison": {
                    "supported_filters": ["month", "business_group", "product_line_5"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                },
                "get_entity_metric_value": {
                    "supported_filters": ["month", "business_group", "product_line_5"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                    "description": "Lookup one real-data entity metric for one explicit month.",
                },
                "get_entity_month_table": {
                    "supported_filters": ["month", "business_group"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                    "description": "List all entities for one explicit month and metric, preserving inventory_only and revenue_only rows.",
                },
                "get_entity_period_pair_table": {
                    "supported_filters": ["business_group"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                    "description": "List all entities for two explicit periods without falling back to latest months.",
                },
                "get_entity_multi_month_table": {
                    "supported_filters": ["business_group"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                    "description": "List all entities by month across an explicit date range.",
                },
                "get_entity_period_pair_value": {
                    "supported_filters": ["business_group"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                    "description": "Lookup one entity across two explicit periods without falling back to latest months.",
                },
                "get_entity_metric_ranking": {
                    "supported_filters": ["month", "business_group", "product_line_5"],
                    "supported_metrics": [
                        "revenue_amount",
                        "inventory_amount",
                        "inventory_qty",
                        "revenue_inventory_amount_ratio",
                        "health_score",
                        "risk_score",
                    ],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                    "description": "Rank real-data entities by a single metric at latest/common month grain.",
                },
                "get_entity_period_pair_comparison": {
                    "supported_filters": ["business_group"],
                    "supported_metrics": ["revenue", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                },
                "get_entity_time_series": {
                    "supported_filters": ["business_group", "product_line_5"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                },
                "get_overall_time_series": {
                    "supported_filters": [],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["overall"],
                    "available": not self.context.artifacts.monthly_revenue.empty,
                },
                "get_entity_trend_comparison": {
                    "supported_filters": ["business_group", "product_line_5"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                },
                "get_revenue_inventory_relationship": {
                    "supported_filters": ["month", "business_group", "product_line_5"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                },
                "get_entity_contribution_analysis": {
                    "supported_filters": ["business_group", "product_line_5"],
                    "supported_metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"],
                    "supported_dimensions": ["business_group", "product_line_5"],
                    "available": not self.context.artifacts.revenue_inventory_aligned.empty,
                },
                "get_anomalies": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": True,
                },
                "get_yoy_mom_breakdown": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "supported_metrics": ["revenue", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["platform", "business_group", "overall"],
                    "available": self._tool_has_current_previous_period("revenue"),
                },
                "get_contribution_analysis": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "supported_metrics": ["revenue", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["platform", "business_group"],
                    "available": self._tool_has_current_previous_period("revenue"),
                },
                "get_inventory_turnover_proxy": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": not self.context.artifacts.platform_monthly_analysis.empty,
                    "description": "Inventory efficiency proxy derived from revenue and inventory data only.",
                },
                "get_platform_performance_snapshot": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": not self.context.artifacts.platform_monthly_analysis.empty,
                    "description": "Deterministic platform scorecard using revenue scale, revenue momentum, inventory-efficiency proxy, and anomaly signals.",
                },
                "get_period_pair_metric_comparison": {
                    "supported_filters": ["platform", "group_code"],
                    "supported_metrics": ["revenue", "inventory_amount", "inventory_qty"],
                    "supported_dimensions": ["overall", "platform", "business_group"],
                    "available": not self.context.artifacts.monthly_revenue.empty,
                    "description": "Compare one metric between two explicit periods with optional platform or business-group breakdown.",
                },
                "get_root_cause_candidates": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "supported_metrics": ["revenue"],
                    "available": (
                        self._tool_has_current_previous_period("revenue")
                        or not self.context.artifacts.platform_monthly_analysis.empty
                    ),
                    "description": "Return deterministic candidate observations for possible drivers without claiming causal root cause.",
                },
                "get_correlations": {
                    "supported_filters": [],
                    "available": not self.context.artifacts.correlation_analysis.empty,
                },
                "get_chart_catalog": {
                    "supported_filters": [],
                    "available": True,
                },
                "get_chart_payload": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": True,
                },
                "get_chart_table": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": True,
                },
                "get_observation_options": {
                    "supported_filters": [],
                    "available": True,
                },
                "get_observation_table": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": True,
                },
                "create_chart_image": {
                    "supported_filters": ["month", "platform", "group_code"],
                    "available": True,
                },
            },
        }
        logger.info("Completed tool get_tool_capability_matrix")
        return result

    def get_metric_table(self, metric: str, filters: QueryFilters | None = None) -> pd.DataFrame:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_metric_table for metric=%s", metric)
        filters = filters or QueryFilters()

        unsupported_filters = self._unsupported_filters(metric, filters)
        if unsupported_filters:
            logger.warning(
                "Metric %s does not support filters=%s. Returning empty result instead of silently ignoring them.",
                metric,
                unsupported_filters,
            )
            return self._empty_metric_frame(metric)

        if metric == "revenue_trend":
            df = self._build_revenue_trend(filters)
        elif metric == "inventory_amount_trend":
            df = self._build_inventory_trend("金額", filters)
        elif metric == "inventory_qty_trend":
            df = self._build_inventory_trend("QTY", filters)
        else:
            metric_mapping = {
                "revenue_monthly": self.context.artifacts.monthly_revenue,
                "inventory_amount_monthly": self.context.artifacts.monthly_inventory_amount,
                "inventory_qty_monthly": self.context.artifacts.monthly_inventory_qty,
                "revenue_by_group": self.context.artifacts.revenue_by_group,
                "inventory_by_group": self.context.artifacts.inventory_by_group,
                "platform_monthly": self.context.artifacts.platform_monthly_analysis,
                "anomalies": self.context.artifacts.anomalies,
                "correlations": self.context.artifacts.correlation_analysis,
            }
            df = metric_mapping.get(metric)

        if df is None:
            logger.warning("Unknown metric requested: %s", metric)
            return pd.DataFrame()

        filtered = self._apply_filters(df, filters)
        logger.info("Completed tool get_metric_table for metric=%s with rows=%s", metric, len(filtered))
        return filtered

    def get_top_groups(self, metric: str, top_n: int = 5, filters: QueryFilters | None = None) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_top_groups for metric=%s top_n=%s", metric, top_n)
        filters = filters or QueryFilters()

        if metric not in {"revenue", "inventory"}:
            logger.warning("Unsupported metric for get_top_groups: %s", metric)
            return []

        value_column = "營收" if metric == "revenue" else "金額"
        source_df = self.context.artifacts.revenue_enriched if metric == "revenue" else self.context.artifacts.inventory_enriched
        filtered_source = self._apply_filters(source_df, filters)

        if filtered_source.empty:
            logger.info("Completed tool get_top_groups with rows=0")
            return []

        grouped = (
            filtered_source.groupby(["新事業群", "事業群名稱"], dropna=False, as_index=False)[value_column]
            .sum(min_count=1)
            .sort_values(value_column, ascending=False)
            .reset_index(drop=True)
        )

        result: list[dict[str, Any]] = []
        for _, row in grouped.head(top_n).iterrows():
            result.append(
                {
                    "group_code": row.get("新事業群"),
                    "group_name": row.get("事業群名稱"),
                    "metric": value_column,
                    "value": row.get(value_column),
                    "value_text": format_number(row.get(value_column)),
                }
            )
        logger.info("Completed tool get_top_groups with rows=%s", len(result))
        return result

    def get_entity_performance_snapshot(
        self,
        entity_dimension: str = "business_group",
        month: str | None = None,
        parent_filter: dict[str, Any] | None = None,
        filters: QueryFilters | None = None,
        top_n: int | None = None,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_entity_performance_snapshot dimension=%s month=%s top_n=%s",
            entity_dimension,
            month,
            top_n,
        )
        filters = filters or QueryFilters()
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        current_month = month or filters.month or self._latest_common_month()
        limitations = [
            f"這是 deterministic {label} performance scorecard，使用營收規模、營收動能、營收/庫存 proxy 與資料完整性評分。",
                "營收/庫存為 proxy 指標，非正式周轉指標。",
            "只在 revenue 與 inventory 同時存在且分母合法時才計算 ratio。",
        ]
        rubric = {
            "revenue_scale_weight": 0.30,
            "revenue_momentum_weight": 0.20,
            "inventory_efficiency_weight": 0.35,
            "data_completeness_weight": 0.15,
        }
        if not current_month:
            return {
                "month": None,
                "dimension": dimension,
                "entity_dimension": dimension,
                "entity_label": label,
                "rows": [],
                "summary": {},
                "rubric": rubric,
                "limitations": limitations + ["目前沒有可共同對齊的月份。"],
            }

        current_rows = self._entity_snapshot_rows(dimension, current_month, parent_filter, filters)
        if not current_rows:
            return {
                "month": current_month,
                "dimension": dimension,
                "entity_dimension": dimension,
                "entity_label": label,
                "rows": [],
                "summary": {},
                "rubric": rubric,
                "limitations": limitations + [f"{current_month} 沒有可用的 {label} 對齊資料。"],
            }

        previous_month = self._previous_common_month(current_month, dimension, parent_filter, filters)
        previous_by_entity: dict[str, float] = {}
        if previous_month:
            previous_rows = self._entity_snapshot_rows(dimension, previous_month, parent_filter, filters)
            previous_by_entity = {
                str(row["entity_value"]): float(row["revenue"])
                for row in previous_rows
                if row.get("revenue") is not None
            }
        else:
            limitations.append("缺少上一個可比較月份，營收動能不納入部分 health_score。")

        for row in current_rows:
            previous_revenue = previous_by_entity.get(str(row["entity_value"]))
            row["previous_revenue"] = previous_revenue
            row["revenue_mom_change"] = self._safe_ratio(
                (row.get("revenue") or 0.0) - previous_revenue,
                previous_revenue,
            ) if previous_revenue is not None else None

        revenue_scores = self._score_by_entity(current_rows, "revenue", higher_is_better=True)
        momentum_scores = self._score_by_entity(current_rows, "revenue_mom_change", higher_is_better=True)
        efficiency_scores = self._score_by_entity(current_rows, "revenue_inventory_amount_ratio", higher_is_better=True)
        completeness_scores = self._score_by_entity(current_rows, "both_row_share", higher_is_better=True)
        revenue_ranks = self._rank_by_entity(current_rows, "revenue", descending=True)
        inventory_ranks = self._rank_by_entity(current_rows, "inventory_amount", descending=True)
        efficiency_ranks = self._rank_by_entity(current_rows, "revenue_inventory_amount_ratio", descending=True)

        rows: list[dict[str, Any]] = []
        for row in current_rows:
            entity_value = str(row["entity_value"])
            component_scores = {
                "revenue_scale_score": revenue_scores.get(entity_value),
                "revenue_momentum_score": momentum_scores.get(entity_value),
                "inventory_efficiency_score": efficiency_scores.get(entity_value),
                "data_completeness_score": completeness_scores.get(entity_value),
            }
            health_score = self._entity_health_score(component_scores, rubric)
            row.update(
                {
                    "revenue_amount": row.get("revenue"),
                    "revenue_rank": revenue_ranks.get(entity_value),
                    "inventory_rank": inventory_ranks.get(entity_value),
                    "efficiency_rank": efficiency_ranks.get(entity_value),
                    "anomaly_count": int(row.get("anomaly_count") or 0),
                    "health_score": health_score,
                    "risk_score": round(1.0 - health_score, 4) if health_score is not None else None,
                    "performance_label": self._performance_label(health_score),
                    "primary_strength": self._entity_primary_strength(row, label),
                    "primary_risk": self._entity_primary_risk(row, label),
                    **component_scores,
                }
            )
            rows.append(row)

        rows = sorted(rows, key=lambda item: (item.get("health_score") is None, -(item.get("health_score") or 0.0), item.get("entity_value") or ""))
        if top_n is not None:
            rows = rows[: max(int(top_n), 0)]

        summary = self._entity_snapshot_summary(rows, dimension)
        if any(is_unmapped_entity(row.get("entity_value")) for row in rows):
            limitations.append("部分資料列的新事業群或五大產品線為未對應，已作為資料品質限制處理。")
        result = {
            "evidence_type": "entity_performance_snapshot",
            "source_tool": "get_entity_performance_snapshot",
            "month": current_month,
            "dimension": dimension,
            "entity_dimension": dimension,
            "entity_label": label,
            "parent_filter": parent_filter or {},
            "rows": rows,
            "summary": summary,
            "rubric": rubric,
            "limitations": list(dict.fromkeys(limitations)),
        }
        logger.info("Completed tool get_entity_performance_snapshot with rows=%s", len(rows))
        return result

    def get_entity_cross_section_comparison(
        self,
        entity_dimension: str = "business_group",
        month: str | None = None,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = self.get_entity_performance_snapshot(
            entity_dimension=entity_dimension,
            month=month,
            parent_filter=parent_filter,
        )
        return {
            "evidence_type": "entity_cross_section_comparison",
            "source_tool": "get_entity_cross_section_comparison",
            "month": snapshot.get("month"),
            "dimension": snapshot.get("dimension"),
            "entity_dimension": snapshot.get("entity_dimension"),
            "entity_label": snapshot.get("entity_label"),
            "parent_filter": snapshot.get("parent_filter", {}),
            "rows": snapshot.get("rows", []),
            "summary": snapshot.get("summary", {}),
            "rubric": snapshot.get("rubric", {}),
            "limitations": snapshot.get("limitations", []),
        }

    def get_entity_metric_value(
        self,
        entity_dimension: str,
        entity_value: str,
        metric: str,
        month: str | None = None,
    ) -> dict[str, Any]:
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        df = self._entity_aligned_frame(dimension, None, QueryFilters())
        limitations: list[str] = []
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收相對庫存效率為 proxy，非正式庫存週轉率。")
        if df.empty or dimension not in df.columns:
            return {
                "evidence_type": "entity_metric_lookup",
                "source_tool": "get_entity_metric_value",
                "month": month,
                "entity_dimension": dimension,
                "entity_label": label,
                "entity_value": entity_value,
                "metric": metric_key,
                "metric_label": metric_label,
                "value": None,
                "limitations": limitations + ["目前沒有可用的 entity 對齊資料。"],
            }

        candidates = sorted(df[dimension].dropna().astype(str).unique().tolist())
        resolved_value = resolve_entity_value(entity_value, dimension, candidates) or entity_value
        lookup_month = month or self._latest_common_month()
        scoped = df[
            (df["month_key"].astype(str) == str(lookup_month))
            & (df[dimension].astype(str) == str(resolved_value))
        ].copy()
        if scoped.empty or metric_key not in scoped.columns:
            return {
                "evidence_type": "entity_metric_lookup",
                "source_tool": "get_entity_metric_value",
                "month": lookup_month,
                "entity_dimension": dimension,
                "entity_label": label,
                "entity_value": resolved_value,
                "metric": metric_key,
                "metric_label": metric_label,
                "value": None,
                "limitations": limitations + [f"{lookup_month} 找不到 {label} {resolved_value} 的 {metric_label} 資料。"],
            }

        value = self._normalize_number(scoped[metric_key].sum(min_count=1))
        return {
            "evidence_type": "entity_metric_lookup",
            "source_tool": "get_entity_metric_value",
            "month": lookup_month,
            "entity_dimension": dimension,
            "entity_label": label,
            "entity_value": resolved_value,
            "metric": metric_key,
            "metric_label": metric_label,
            "value": value,
            "limitations": limitations,
        }

    def get_entity_month_table(
        self,
        entity_dimension: str,
        metric: str,
        month: str,
        parent_filter: dict[str, Any] | None = None,
        include_qty: bool = True,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_entity_month_table dimension=%s metric=%s month=%s",
            entity_dimension,
            metric,
            month,
        )
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        if metric_key == "revenue_inventory_amount_ratio":
            metric_key = "revenue_amount"
            metric_label = "營收"
        lookup_month = month or self._latest_common_month()
        limitations: list[str] = []
        if not lookup_month:
            return {
                "evidence_type": "entity_month_table",
                "source_tool": "get_entity_month_table",
                "month": lookup_month,
                "entity_dimension": dimension,
                "entity_label": label,
                "metric": metric_key,
                "metric_label": metric_label,
                "rows": [],
                "summary": {},
                "limitations": ["目前沒有可用月份。"],
            }

        source_rows = self._entity_snapshot_rows(dimension, str(lookup_month), parent_filter, QueryFilters())
        rows: list[dict[str, Any]] = []
        for row in source_rows:
            value = self._normalize_number(row.get(metric_key))
            if value is None:
                continue
            presence_counts = row.get("data_presence_counts") or {}
            output_row = {
                "month": lookup_month,
                "entity_dimension": dimension,
                "entity_label": label,
                "entity_value": row.get("entity_value"),
                "value": value,
                "metric": metric_key,
                "metric_label": metric_label,
                "revenue_amount": row.get("revenue_amount"),
                "inventory_amount": row.get("inventory_amount"),
                "data_presence_flag": self._dominant_presence_flag(presence_counts),
            }
            if include_qty:
                output_row["inventory_qty"] = row.get("inventory_qty")
            rows.append(output_row)

        rows = sorted(rows, key=lambda item: float(item.get("value") or 0), reverse=True)
        if any(is_unmapped_entity(row.get("entity_value")) for row in rows):
            limitations.append("部分資料列的事業群或產品線為未對應，已作為資料品質限制處理。")
        if not rows:
            limitations.append(f"{lookup_month} 找不到各{label}的{metric_label}資料。")

        top = rows[0] if rows else {}
        lowest_candidates = [row for row in rows if not is_unmapped_entity(row.get("entity_value"))]
        lowest = sorted(lowest_candidates, key=lambda item: float(item.get("value") or 0))[0] if lowest_candidates else (rows[-1] if rows else {})
        summary = {
            "row_count": len(rows),
            "top_entity": top.get("entity_value"),
            "top_value": top.get("value"),
            "lowest_entity": lowest.get("entity_value"),
            "lowest_value": lowest.get("value"),
        }
        result = {
            "evidence_type": "entity_month_table",
            "source_tool": "get_entity_month_table",
            "month": lookup_month,
            "entity_dimension": dimension,
            "entity_label": label,
            "metric": metric_key,
            "metric_label": metric_label,
            "parent_filter": parent_filter or {},
            "rows": rows,
            "summary": summary,
            "limitations": limitations,
        }
        logger.info("Completed tool get_entity_month_table with rows=%s", len(rows))
        return result

    def get_entity_period_pair_table(
        self,
        entity_dimension: str,
        metric: str,
        period_a: str,
        period_b: str,
        parent_filter: dict[str, Any] | None = None,
        include_change: bool = True,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_entity_period_pair_table dimension=%s metric=%s period_a=%s period_b=%s",
            entity_dimension,
            metric,
            period_a,
            period_b,
        )
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        limitations = ["期間比較為描述性差異，不宣稱 root cause。"]
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收相對庫存效率為 proxy，非正式庫存週轉率。")
        if not period_a or not period_b:
            return {
                "evidence_type": "entity_period_pair_table",
                "source_tool": "get_entity_period_pair_table",
                "period_a": period_a,
                "period_b": period_b,
                "entity_dimension": dimension,
                "entity_label": label,
                "metric": metric_key,
                "metric_label": metric_label,
                "parent_filter": parent_filter or {},
                "rows": [],
                "summary": {},
                "limitations": limitations + ["缺少 period_a 或 period_b，未改用最新月份 fallback。"],
            }

        rows_a = {str(row.get("entity_value")): row for row in self._entity_snapshot_rows(dimension, str(period_a), parent_filter, QueryFilters())}
        rows_b = {str(row.get("entity_value")): row for row in self._entity_snapshot_rows(dimension, str(period_b), parent_filter, QueryFilters())}
        entity_values = sorted(set(rows_a) | set(rows_b))
        rows: list[dict[str, Any]] = []
        for entity_value in entity_values:
            row_a = rows_a.get(entity_value, {})
            row_b = rows_b.get(entity_value, {})
            value_a = self._normalize_number(row_a.get(metric_key))
            value_b = self._normalize_number(row_b.get(metric_key))
            if value_a is None and value_b is None:
                continue
            change = None
            change_pct = None
            if include_change and value_a is not None and value_b is not None:
                change = self._normalize_number(float(value_b) - float(value_a))
                change_pct = self._safe_ratio(change, value_a)
            presence_counts: dict[str, int] = {}
            for source in [row_a.get("data_presence_counts"), row_b.get("data_presence_counts")]:
                if isinstance(source, dict):
                    for key, value in source.items():
                        presence_counts[str(key)] = presence_counts.get(str(key), 0) + int(value or 0)
            rows.append(
                {
                    "entity_dimension": dimension,
                    "entity_label": label,
                    "entity_value": entity_value,
                    "value_a": value_a,
                    "value_b": value_b,
                    "change": change,
                    "change_pct": change_pct,
                    "data_presence_flag": self._dominant_presence_flag(presence_counts),
                    "revenue_amount_a": row_a.get("revenue_amount"),
                    "revenue_amount_b": row_b.get("revenue_amount"),
                    "inventory_amount_a": row_a.get("inventory_amount"),
                    "inventory_amount_b": row_b.get("inventory_amount"),
                    "inventory_qty_a": row_a.get("inventory_qty"),
                    "inventory_qty_b": row_b.get("inventory_qty"),
                }
            )
        rows = sorted(rows, key=lambda item: (item.get("value_b") is None, -(float(item.get("value_b") or 0))))
        mapped_rows = [row for row in rows if not is_unmapped_entity(row.get("entity_value"))]
        summary_candidates = mapped_rows or rows
        top_b = next((row for row in summary_candidates if row.get("value_b") is not None), None)
        increases = [row for row in summary_candidates if row.get("change") is not None]
        largest_increase = sorted(increases, key=lambda row: float(row.get("change") or 0), reverse=True)[0] if increases else None
        largest_decrease = sorted(increases, key=lambda row: float(row.get("change") or 0))[0] if increases else None
        if not rows:
            limitations.append(f"{period_a} 與 {period_b} 找不到各{label}的{metric_label}資料。")
        result = {
            "evidence_type": "entity_period_pair_table",
            "source_tool": "get_entity_period_pair_table",
            "period_a": period_a,
            "period_b": period_b,
            "entity_dimension": dimension,
            "entity_label": label,
            "metric": metric_key,
            "metric_label": metric_label,
            "parent_filter": parent_filter or {},
            "rows": rows,
            "summary": {
                "row_count": len(rows),
                "top_entity_period_b": top_b.get("entity_value") if top_b else None,
                "largest_increase_entity": largest_increase.get("entity_value") if largest_increase else None,
                "largest_decrease_entity": largest_decrease.get("entity_value") if largest_decrease else None,
            },
            "limitations": list(dict.fromkeys(limitations)),
        }
        logger.info("Completed tool get_entity_period_pair_table with rows=%s", len(rows))
        return result

    def get_entity_multi_month_table(
        self,
        entity_dimension: str,
        metric: str,
        start_month: str,
        end_month: str,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_entity_multi_month_table dimension=%s metric=%s start=%s end=%s",
            entity_dimension,
            metric,
            start_month,
            end_month,
        )
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        limitations = ["僅描述歷史資料，不做 forecast 或 root cause 判定。"]
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收相對庫存效率為 proxy，非正式庫存週轉率。")
        if not start_month or not end_month:
            return {
                "evidence_type": "entity_multi_month_table",
                "source_tool": "get_entity_multi_month_table",
                "start_month": start_month,
                "end_month": end_month,
                "entity_dimension": dimension,
                "entity_label": label,
                "metric": metric_key,
                "metric_label": metric_label,
                "parent_filter": parent_filter or {},
                "rows": [],
                "summary": {},
                "limitations": limitations + ["缺少 start_month 或 end_month，未改用最新月份 fallback。"],
            }
        df = self._entity_aligned_frame(dimension, parent_filter, QueryFilters())
        df = self._apply_month_window(df, recent_n=None, start_month=str(start_month), end_month=str(end_month))
        months = sorted(df["month_key"].dropna().astype(str).unique().tolist()) if not df.empty and "month_key" in df.columns else []
        rows: list[dict[str, Any]] = []
        for month in months:
            for row in self._entity_snapshot_rows(dimension, month, parent_filter, QueryFilters()):
                value = self._normalize_number(row.get(metric_key))
                if value is None:
                    continue
                rows.append(
                    {
                        "month": month,
                        "entity_dimension": dimension,
                        "entity_label": label,
                        "entity_value": row.get("entity_value"),
                        "value": value,
                        "metric": metric_key,
                        "metric_label": metric_label,
                        "revenue_amount": row.get("revenue_amount"),
                        "inventory_amount": row.get("inventory_amount"),
                        "inventory_qty": row.get("inventory_qty"),
                        "data_presence_flag": self._dominant_presence_flag(row.get("data_presence_counts")),
                    }
                )
        rows = sorted(rows, key=lambda item: (item.get("month"), str(item.get("entity_value") or "")))
        if not rows:
            limitations.append(f"{start_month} 至 {end_month} 找不到各{label}的{metric_label}資料。")
        return {
            "evidence_type": "entity_multi_month_table",
            "source_tool": "get_entity_multi_month_table",
            "start_month": start_month,
            "end_month": end_month,
            "entity_dimension": dimension,
            "entity_label": label,
            "metric": metric_key,
            "metric_label": metric_label,
            "parent_filter": parent_filter or {},
            "rows": rows,
            "summary": {"row_count": len(rows), "months": months},
            "limitations": list(dict.fromkeys(limitations)),
        }

    def get_entity_period_pair_value(
        self,
        entity_dimension: str,
        entity_value: str,
        metric: str,
        period_a: str,
        period_b: str,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        resolved_value = resolve_entity_value(entity_value, dimension) or entity_value
        rows_a = self._entity_snapshot_rows(dimension, str(period_a), parent_filter, QueryFilters())
        rows_b = self._entity_snapshot_rows(dimension, str(period_b), parent_filter, QueryFilters())
        row_a = next((row for row in rows_a if str(row.get("entity_value")) == str(resolved_value)), {})
        row_b = next((row for row in rows_b if str(row.get("entity_value")) == str(resolved_value)), {})
        value_a = self._normalize_number(row_a.get(metric_key))
        value_b = self._normalize_number(row_b.get(metric_key))
        change = self._normalize_number(float(value_b) - float(value_a)) if value_a is not None and value_b is not None else None
        change_pct = self._safe_ratio(change, value_a) if change is not None else None
        limitations = ["期間比較為描述性差異，不宣稱 root cause。"]
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收相對庫存效率為 proxy，非正式庫存週轉率。")
        if value_a is None and value_b is None:
            limitations.append(f"找不到 {resolved_value} 在 {period_a} 或 {period_b} 的{metric_label}資料。")
        return {
            "evidence_type": "entity_period_pair_value",
            "source_tool": "get_entity_period_pair_value",
            "period_a": period_a,
            "period_b": period_b,
            "entity_dimension": dimension,
            "entity_label": label,
            "entity_value": resolved_value,
            "metric": metric_key,
            "metric_label": metric_label,
            "value_a": value_a,
            "value_b": value_b,
            "change": change,
            "change_pct": change_pct,
            "parent_filter": parent_filter or {},
            "rows": [
                {"month": period_a, "value": value_a, "metric": metric_key, "metric_label": metric_label},
                {"month": period_b, "value": value_b, "metric": metric_key, "metric_label": metric_label},
            ],
            "summary": {"direction": self._change_direction(change)},
            "limitations": list(dict.fromkeys(limitations)),
        }

    def get_entity_metric_ranking(
        self,
        entity_dimension: str = "business_group",
        metric: str = "revenue_amount",
        month: str | None = None,
        top_n: int = 5,
        parent_filter: dict[str, Any] | None = None,
        sort_direction: str | None = None,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_entity_metric_ranking dimension=%s metric=%s month=%s top_n=%s",
            entity_dimension,
            metric,
            month,
            top_n,
        )
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key = self._normalize_entity_ranking_metric(metric)
        metric_label = self._entity_ranking_metric_label(metric_key)
        direction = self._entity_metric_sort_direction(metric_key, sort_direction)
        snapshot = self.get_entity_performance_snapshot(
            entity_dimension=dimension,
            month=month,
            parent_filter=parent_filter,
        )
        ranking_month = snapshot.get("month")
        limitations = list(snapshot.get("limitations") or [])
        source_rows = list(snapshot.get("rows") or [])
        rows: list[dict[str, Any]] = []
        for row in source_rows:
            value = self._normalize_number(row.get(metric_key))
            if value is None:
                continue
            rows.append(
                {
                    "month": ranking_month,
                    "entity_dimension": dimension,
                    "entity_label": label,
                    "entity_value": row.get("entity_value"),
                    "value": value,
                    "metric": metric_key,
                    "metric_label": metric_label,
                    "health_score": row.get("health_score"),
                    "risk_score": row.get("risk_score"),
                    "data_presence": row.get("data_presence_counts"),
                    "data_presence_flag": self._dominant_presence_flag(row.get("data_presence_counts")),
                    "revenue_amount": row.get("revenue_amount"),
                    "inventory_amount": row.get("inventory_amount"),
                    "inventory_qty": row.get("inventory_qty"),
                    "revenue_inventory_amount_ratio": row.get("revenue_inventory_amount_ratio"),
                }
            )

        reverse = direction == "descending"
        rows = sorted(
            rows,
            key=lambda row: (
                row.get("value") is None,
                -(float(row["value"])) if reverse else float(row["value"]),
                is_unmapped_entity(row.get("entity_value")),
                str(row.get("entity_value") or ""),
            ),
        )
        for index, row in enumerate(rows, start=1):
            row["rank"] = index

        top_row = next((row for row in rows if not is_unmapped_entity(row.get("entity_value"))), None)
        if top_row is None and rows:
            top_row = rows[0]
        if rows and any(is_unmapped_entity(row.get("entity_value")) for row in rows):
            limitations.append(f"部分{label}為未對應，未對應資料列保留於 ranking rows，但不優先作為正式 top entity。")
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收/庫存為 proxy 指標，非正式周轉指標；ratio 為空的 entity 已排除。")

        limited_rows = rows[: max(int(top_n or 0), 0)]
        result = {
            "evidence_type": "entity_metric_ranking",
            "source_tool": "get_entity_metric_ranking",
            "month": ranking_month,
            "dimension": dimension,
            "entity_dimension": dimension,
            "entity_label": label,
            "metric": metric_key,
            "metric_label": metric_label,
            "sort_direction": direction,
            "parent_filter": parent_filter or {},
            "rows": limited_rows,
            "top_entity": top_row.get("entity_value") if top_row else None,
            "top_value": top_row.get("value") if top_row else None,
            "limitations": list(dict.fromkeys(limitations)),
        }
        logger.info("Completed tool get_entity_metric_ranking with rows=%s", len(limited_rows))
        return result

    def get_entity_period_pair_comparison(
        self,
        entity_dimension: str = "business_group",
        metric: str = "revenue",
        period_a: str | None = None,
        period_b: str | None = None,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dimension = self._normalize_entity_dimension(entity_dimension)
        metric_column = {
            "revenue": "revenue_amount",
            "inventory_amount": "inventory_amount",
            "inventory_qty": "inventory_qty",
        }.get(metric)
        aligned = self._entity_aligned_frame(dimension, parent_filter, QueryFilters())
        if metric_column is None:
            return {"metric": metric, "dimension": dimension, "overall": {}, "breakdown": [], "limitations": [f"Unsupported metric: {metric}"]}
        months = sorted(aligned["month_key"].dropna().astype(str).unique().tolist()) if not aligned.empty else []
        period_b = period_b or (months[-1] if months else None)
        if period_a is None and period_b in months:
            index = months.index(period_b)
            period_a = months[index - 1] if index > 0 else None
        if not period_a or not period_b:
            return {"metric": metric, "dimension": dimension, "overall": {}, "breakdown": [], "limitations": ["缺少可比較期間。"]}

        entity_column = dimension
        grouped = (
            aligned[aligned["month_key"].isin([period_a, period_b])]
            .groupby(["month_key", entity_column], dropna=False)[metric_column]
            .sum(min_count=1)
            .reset_index()
        )
        overall = self._period_pair_values(grouped.rename(columns={"month_key": COL_MONTH, metric_column: COL_REVENUE}), COL_REVENUE, period_a, period_b)
        breakdown: list[dict[str, Any]] = []
        for entity in sorted(grouped[entity_column].dropna().astype(str).unique().tolist()):
            subset = grouped[grouped[entity_column].astype(str) == entity].rename(columns={"month_key": COL_MONTH, metric_column: COL_REVENUE})
            values = self._period_pair_values(subset, COL_REVENUE, period_a, period_b)
            if values:
                breakdown.append({"name": entity, "entity_value": entity, **values})
        breakdown = sorted(breakdown, key=lambda item: abs(float(item.get("change") or 0.0)), reverse=True)
        return {
            "evidence_type": "entity_period_pair_comparison",
            "source_tool": "get_entity_period_pair_comparison",
            "metric": metric,
            "period_a": period_a,
            "period_b": period_b,
            "dimension": dimension,
            "entity_dimension": dimension,
            "entity_label": ENTITY_LABELS[dimension],
            "overall": overall,
            "breakdown": breakdown,
            "limitations": ["期間比較為描述性差異，不宣稱 root cause。"],
        }

    def get_entity_time_series(
        self,
        entity_dimension: str,
        entity_value: str,
        metric: str,
        recent_n: int | None = None,
        start_month: str | None = None,
        end_month: str | None = None,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        df = self._entity_aligned_frame(dimension, parent_filter, QueryFilters())
        limitations = ["僅描述歷史資料，不做 forecast 或 root cause 判定。"]
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收相對庫存效率為 proxy，非正式庫存週轉率。")
        if df.empty or dimension not in df.columns:
            return {
                "evidence_type": "entity_time_series",
                "source_tool": "get_entity_time_series",
                "entity_dimension": dimension,
                "entity_label": label,
                "entity_value": entity_value,
                "metric": metric_key,
                "metric_label": metric_label,
                "rows": [],
                "summary": {},
                "parent_filter": parent_filter or {},
                "limitations": limitations + ["目前沒有可用的對齊資料。"],
            }

        scoped = df[df[dimension].astype(str) == str(entity_value)].copy()
        scoped = self._apply_month_window(scoped, recent_n=recent_n, start_month=start_month, end_month=end_month)
        rows = self._build_entity_series_rows(scoped, metric_key)
        if not rows:
            return {
                "evidence_type": "entity_time_series",
                "source_tool": "get_entity_time_series",
                "entity_dimension": dimension,
                "entity_label": label,
                "entity_value": entity_value,
                "metric": metric_key,
                "metric_label": metric_label,
                "rows": [],
                "summary": {},
                "parent_filter": parent_filter or {},
                "limitations": limitations + [f"找不到 {entity_value} 的可比較月份資料。"],
            }
        return {
            "evidence_type": "entity_time_series",
            "source_tool": "get_entity_time_series",
            "entity_dimension": dimension,
            "entity_label": label,
            "entity_value": entity_value,
            "metric": metric_key,
            "metric_label": metric_label,
            "rows": rows,
            "summary": self._series_summary(rows),
            "parent_filter": parent_filter or {},
            "limitations": limitations,
        }

    def get_overall_time_series(
        self,
        metric: str,
        recent_n: int | None = None,
        start_month: str | None = None,
        end_month: str | None = None,
    ) -> dict[str, Any]:
        metric_key, metric_label = self._canonical_metric_spec(metric)
        frame = self._overall_metric_frame(metric_key)
        limitations = ["僅描述歷史資料，不做 forecast 或 root cause 判定。"]
        if frame.empty:
            return {
                "evidence_type": "overall_time_series",
                "source_tool": "get_overall_time_series",
                "metric": metric_key,
                "metric_label": metric_label,
                "rows": [],
                "summary": {},
                "limitations": limitations + ["目前沒有可用的整體月資料。"],
            }
        frame = self._apply_month_window(frame, recent_n=recent_n, start_month=start_month, end_month=end_month, month_column=COL_MONTH)
        frame = frame.rename(columns={COL_MONTH: "month"})
        rows = self._series_rows_from_month_frame(frame, value_column=self._metric_value_column_from_canonical(metric_key))
        return {
            "evidence_type": "overall_time_series",
            "source_tool": "get_overall_time_series",
            "metric": metric_key,
            "metric_label": metric_label,
            "rows": rows,
            "summary": self._series_summary(rows),
            "limitations": limitations,
        }

    def get_entity_trend_comparison(
        self,
        entity_dimension: str,
        metric: str,
        recent_n: int | None = None,
        start_month: str | None = None,
        end_month: str | None = None,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        df = self._entity_aligned_frame(dimension, parent_filter, QueryFilters())
        limitations = ["僅描述歷史資料，不做 forecast 或 root cause 判定。"]
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收相對庫存效率為 proxy，非正式庫存週轉率。")
        if df.empty or dimension not in df.columns:
            return {
                "evidence_type": "entity_trend_comparison",
                "source_tool": "get_entity_trend_comparison",
                "entity_dimension": dimension,
                "entity_label": label,
                "metric": metric_key,
                "metric_label": metric_label,
                "rows": [],
                "entity_summaries": [],
                "summary": {},
                "parent_filter": parent_filter or {},
                "limitations": limitations + ["目前沒有可用的對齊資料。"],
            }
        df = self._apply_month_window(df, recent_n=recent_n, start_month=start_month, end_month=end_month)
        rows: list[dict[str, Any]] = []
        entity_summaries: list[dict[str, Any]] = []
        for entity_value, subset in df.groupby(dimension, dropna=False):
            series_rows = self._build_entity_series_rows(subset, metric_key)
            if not series_rows:
                continue
            rows.extend(
                [
                    {
                        "entity_value": str(entity_value),
                        "entity_dimension": dimension,
                        "entity_label": label,
                        **item,
                    }
                    for item in series_rows
                ]
            )
            summary = self._series_summary(series_rows)
            entity_summaries.append(
                {
                    "entity_value": str(entity_value),
                    "latest_month": summary.get("latest_month"),
                    "latest_value": summary.get("latest_value"),
                    "overall_change": summary.get("overall_change"),
                    "overall_change_pct": summary.get("overall_change_pct"),
                    "direction": summary.get("direction"),
                }
            )
        entity_summaries = sorted(
            entity_summaries,
            key=lambda item: abs(float(item.get("overall_change") or 0.0)),
            reverse=True,
        )
        top_growth = next((item for item in entity_summaries if (item.get("overall_change") or 0) > 0), None)
        return {
            "evidence_type": "entity_trend_comparison",
            "source_tool": "get_entity_trend_comparison",
            "entity_dimension": dimension,
            "entity_label": label,
            "metric": metric_key,
            "metric_label": metric_label,
            "rows": rows,
            "entity_summaries": entity_summaries,
            "summary": {
                "top_growth_entity": top_growth.get("entity_value") if top_growth else None,
                "top_growth_pct": top_growth.get("overall_change_pct") if top_growth else None,
                "latest_month": entity_summaries[0].get("latest_month") if entity_summaries else None,
            },
            "parent_filter": parent_filter or {},
            "limitations": limitations,
        }

    def get_revenue_inventory_relationship(
        self,
        entity_dimension: str,
        recent_n: int | None = None,
        month: str | None = None,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        df = self._entity_aligned_frame(dimension, parent_filter, QueryFilters())
        limitations = [
            "僅根據營收與庫存的歷史變化判讀關係，不做 root cause claim。",
            "營收相對庫存效率為 proxy，非正式庫存週轉率。",
        ]
        if df.empty or dimension not in df.columns:
            return {
                "evidence_type": "metric_relationship",
                "source_tool": "get_revenue_inventory_relationship",
                "entity_dimension": dimension,
                "entity_label": label,
                "rows": [],
                "summary": {},
                "parent_filter": parent_filter or {},
                "limitations": limitations + ["目前沒有可用的對齊資料。"],
            }
        df = self._apply_month_window(df, recent_n=recent_n, start_month=None, end_month=month)
        rows: list[dict[str, Any]] = []
        for entity_value, subset in df.groupby(dimension, dropna=False):
            series = self._build_entity_series_rows(subset, "revenue_amount")
            inventory_series = {row["month"]: row for row in self._build_entity_series_rows(subset, "inventory_amount")}
            ratio_series = {row["month"]: row for row in self._build_entity_series_rows(subset, "revenue_inventory_amount_ratio")}
            if len(series) < 2:
                continue
            latest = series[-1]
            previous = series[-2]
            inv_latest = inventory_series.get(latest["month"])
            inv_previous = inventory_series.get(previous["month"])
            ratio_latest = ratio_series.get(latest["month"])
            ratio_previous = ratio_series.get(previous["month"])
            revenue_change = latest.get("mom_change")
            inventory_change = inv_latest.get("mom_change") if inv_latest else None
            ratio_change = None
            if ratio_latest and ratio_previous:
                ratio_change = (ratio_latest.get("value") or 0.0) - (ratio_previous.get("value") or 0.0)
            label_name = self._relationship_label(revenue_change, inventory_change, ratio_change)
            rows.append(
                {
                    "entity_value": str(entity_value),
                    "entity_dimension": dimension,
                    "entity_label": label,
                    "month": latest["month"],
                    "previous_month": previous["month"],
                    "relationship_label": label_name,
                    "revenue_change": revenue_change,
                    "inventory_change": inventory_change,
                    "ratio_change": ratio_change,
                    "latest_ratio": ratio_latest.get("value") if ratio_latest else None,
                }
            )
        relationship_counts: dict[str, int] = {}
        for row in rows:
            relationship_counts[row["relationship_label"]] = relationship_counts.get(row["relationship_label"], 0) + 1
        return {
            "evidence_type": "metric_relationship",
            "source_tool": "get_revenue_inventory_relationship",
            "entity_dimension": dimension,
            "entity_label": label,
            "rows": rows,
            "summary": {"relationship_counts": relationship_counts},
            "parent_filter": parent_filter or {},
            "limitations": limitations,
        }

    def get_entity_contribution_analysis(
        self,
        entity_dimension: str,
        metric: str,
        period_a: str,
        period_b: str,
        parent_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        dimension = self._normalize_entity_dimension(entity_dimension)
        label = ENTITY_LABELS[dimension]
        metric_key, metric_label = self._canonical_metric_spec(metric)
        df = self._entity_aligned_frame(dimension, parent_filter, QueryFilters())
        limitations = ["期間變化只做描述性 contribution 分析，不做 root cause claim。"]
        if metric_key == "revenue_inventory_amount_ratio":
            limitations.append("營收相對庫存效率為 proxy，非正式庫存週轉率。")
        if df.empty or dimension not in df.columns:
            return {
                "evidence_type": "entity_contribution_analysis",
                "source_tool": "get_entity_contribution_analysis",
                "entity_dimension": dimension,
                "entity_label": label,
                "metric": metric_key,
                "metric_label": metric_label,
                "period_a": period_a,
                "period_b": period_b,
                "rows": [],
                "summary": {},
                "parent_filter": parent_filter or {},
                "limitations": limitations + ["目前沒有可用的對齊資料。"],
            }
        metric_column = self._aligned_metric_value_for_month(df, metric_key, group_dimension=dimension)
        scoped = metric_column[metric_column["month"].isin([period_a, period_b])].copy()
        if scoped.empty:
            return {
                "evidence_type": "entity_contribution_analysis",
                "source_tool": "get_entity_contribution_analysis",
                "entity_dimension": dimension,
                "entity_label": label,
                "metric": metric_key,
                "metric_label": metric_label,
                "period_a": period_a,
                "period_b": period_b,
                "rows": [],
                "summary": {},
                "parent_filter": parent_filter or {},
                "limitations": limitations + ["指定期間沒有可比較資料。"],
            }
        pivot = scoped.pivot_table(index=dimension, columns="month", values="value", aggfunc="sum").fillna(0.0)
        total_change = float(pivot.get(period_b, pd.Series(dtype=float)).sum() - pivot.get(period_a, pd.Series(dtype=float)).sum())
        rows: list[dict[str, Any]] = []
        for entity_value, row in pivot.iterrows():
            value_a = float(row.get(period_a, 0.0))
            value_b = float(row.get(period_b, 0.0))
            change = value_b - value_a
            rows.append(
                {
                    "entity_value": str(entity_value),
                    "value_a": round(value_a, 2),
                    "value_b": round(value_b, 2),
                    "change": round(change, 2),
                    "change_pct": self._safe_ratio(change, value_a),
                    "contribution_pct": self._safe_ratio(change, total_change),
                    "direction": "up" if change > 0 else ("down" if change < 0 else "flat"),
                }
            )
        rows = sorted(rows, key=lambda item: abs(float(item.get("change") or 0.0)), reverse=True)
        top_row = rows[0] if rows else None
        return {
            "evidence_type": "entity_contribution_analysis",
            "source_tool": "get_entity_contribution_analysis",
            "entity_dimension": dimension,
            "entity_label": label,
            "metric": metric_key,
            "metric_label": metric_label,
            "period_a": period_a,
            "period_b": period_b,
            "rows": rows,
            "summary": {
                "top_contributor": top_row.get("entity_value") if top_row else None,
                "top_change": top_row.get("change") if top_row else None,
                "total_change": round(total_change, 2),
            },
            "parent_filter": parent_filter or {},
            "limitations": limitations,
        }

    def get_platform_ranking(
        self,
        metric: str,
        top_n: int = 5,
        filters: QueryFilters | None = None,
    ) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_platform_ranking for metric=%s top_n=%s", metric, top_n)
        filters = filters or QueryFilters()

        value_column_map = {
            "revenue": COL_REVENUE,
            "inventory_amount": COL_INV_AMOUNT,
            "inventory_qty": COL_INV_QTY,
        }
        value_column = value_column_map.get(metric)
        if value_column is None:
            logger.warning("Unsupported metric for get_platform_ranking: %s", metric)
            return []

        df = self.get_metric_table("platform_monthly", filters)
        if df.empty or COL_PLATFORM not in df.columns or value_column not in df.columns:
            logger.info("Completed tool get_platform_ranking with rows=0")
            return []

        grouped = (
            df.groupby(COL_PLATFORM, dropna=False, as_index=False)[value_column]
            .sum(min_count=1)
            .sort_values(value_column, ascending=False)
            .reset_index(drop=True)
        )

        result: list[dict[str, Any]] = []
        for _, row in grouped.head(top_n).iterrows():
            result.append(
                {
                    "dimension": "platform",
                    "platform": row.get(COL_PLATFORM),
                    "metric": metric,
                    "value": row.get(value_column),
                    "value_text": format_number(row.get(value_column), decimals=0 if metric == "inventory_qty" else 2),
                }
            )

        logger.info("Completed tool get_platform_ranking with rows=%s", len(result))
        return result

    def get_platform_ratios(self, filters: QueryFilters | None = None, top_n: int = 5) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_platform_ratios")
        filters = filters or QueryFilters()
        if not getattr(self.context.artifacts, "revenue_inventory_aligned", pd.DataFrame()).empty:
            current_month = filters.month or self._latest_common_month()
            snapshot = self.get_entity_performance_snapshot(
                entity_dimension="business_group",
                month=current_month,
                filters=filters,
            )
            rows: list[dict[str, Any]] = []
            for row in snapshot.get("rows", []):
                if row.get("revenue_inventory_amount_ratio") is None:
                    continue
                rows.append(
                    {
                        "month": row.get("month"),
                        "group_code": row.get("business_group") or row.get("entity_value"),
                        "platform": row.get("business_group") or row.get("entity_value"),
                        "business_group": row.get("business_group") or row.get("entity_value"),
                        "entity_dimension": "business_group",
                        "entity_value": row.get("entity_value"),
                        "revenue": row.get("revenue"),
                        "inventory_amount": row.get("inventory_amount"),
                        "inventory_qty": row.get("inventory_qty"),
                        "revenue_inventory_amount_ratio": row.get("revenue_inventory_amount_ratio"),
                        "revenue_inventory_qty_ratio": row.get("revenue_inventory_qty_ratio"),
                    }
                )
            rows = sorted(rows, key=lambda item: float(item.get("revenue_inventory_amount_ratio") or float("inf")))
            return rows[:top_n]
        df = self.get_metric_table("platform_monthly", filters).copy()
        if df.empty:
            logger.warning(
                "Platform ratio tool unavailable because platform_monthly analysis is empty or not supported by current filters."
            )
            return []

        revenue_amount_ratio = COL_REVENUE_INV_AMOUNT_RATIO
        revenue_qty_ratio = COL_REVENUE_INV_QTY_RATIO
        sort_column = revenue_amount_ratio if revenue_amount_ratio in df.columns else revenue_qty_ratio
        if sort_column not in df.columns:
            logger.warning("Platform ratio columns are missing from platform_monthly analysis.")
            return []

        df = df.sort_values(sort_column, ascending=True)
        results: list[dict[str, Any]] = []
        for _, row in df.head(top_n).iterrows():
            results.append(
                {
                    "month": row.get(COL_MONTH),
                    "group_code": row.get(COL_GROUP_CODE),
                    "platform": row.get(COL_PLATFORM),
                    "revenue": row.get(COL_REVENUE),
                    "inventory_amount": row.get(COL_INV_AMOUNT),
                    "inventory_qty": row.get(COL_INV_QTY),
                    "revenue_inventory_amount_ratio": row.get(revenue_amount_ratio),
                    "revenue_inventory_qty_ratio": row.get(revenue_qty_ratio),
                }
            )
        logger.info("Completed tool get_platform_ratios with rows=%s", len(results))
        return results

    def get_yoy_mom_breakdown(
        self,
        filters: QueryFilters | None = None,
        metric: str = "revenue",
        dimension: str = "platform",
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_yoy_mom_breakdown metric=%s dimension=%s top_n=%s",
            metric,
            dimension,
            top_n,
        )
        filters = filters or QueryFilters()
        if metric not in {"revenue", "inventory_amount", "inventory_qty"}:
            logger.warning("Unsupported metric for get_yoy_mom_breakdown: %s", metric)
            return []
        if dimension not in {"platform", "business_group", "overall"}:
            logger.warning("Unsupported dimension for get_yoy_mom_breakdown: %s", dimension)
            return []

        current_month, previous_month = self._resolve_current_previous_month(metric, filters)
        if not current_month or not previous_month:
            logger.info("Completed tool get_yoy_mom_breakdown with rows=0 due to missing comparable months")
            return []

        current_filters = QueryFilters(
            month=current_month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        previous_filters = QueryFilters(
            month=previous_month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        current_df = self._metric_period_frame(metric, current_filters)
        previous_df = self._metric_period_frame(metric, previous_filters)

        yoy_month = self._shift_year_month(current_month, -1)
        yoy_filters = QueryFilters(
            month=yoy_month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        yoy_df = self._metric_period_frame(metric, yoy_filters) if yoy_month else pd.DataFrame()
        yoy_available = yoy_month is not None and not yoy_df.empty
        yoy_reason = "prior_year_same_month_available" if yoy_available else "prior-year same month data is unavailable"

        rows = self._build_period_breakdown_rows(
            current_df=current_df,
            previous_df=previous_df,
            yoy_df=yoy_df if yoy_available else pd.DataFrame(),
            metric=metric,
            dimension=dimension,
            current_month=current_month,
            previous_month=previous_month,
            yoy_available=yoy_available,
            yoy_reason=yoy_reason,
        )
        rows = sorted(rows, key=lambda item: abs(float(item.get("mom_change") or 0.0)), reverse=True)
        result = rows[:top_n]
        logger.info("Completed tool get_yoy_mom_breakdown with rows=%s", len(result))
        return result

    def get_contribution_analysis(
        self,
        filters: QueryFilters | None = None,
        metric: str = "revenue",
        dimension: str = "platform",
        top_n: int = 5,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_contribution_analysis metric=%s dimension=%s top_n=%s",
            metric,
            dimension,
            top_n,
        )
        filters = filters or QueryFilters()
        if metric not in {"revenue", "inventory_amount", "inventory_qty"}:
            logger.warning("Unsupported metric for get_contribution_analysis: %s", metric)
            return {}
        if dimension not in {"platform", "business_group"}:
            logger.warning("Unsupported dimension for get_contribution_analysis: %s", dimension)
            return {}

        current_month, previous_month = self._resolve_current_previous_month(metric, filters)
        if not current_month or not previous_month:
            logger.info("Completed tool get_contribution_analysis with no comparable months")
            return {}

        current_filters = QueryFilters(
            month=current_month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        previous_filters = QueryFilters(
            month=previous_month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        current_df = self._metric_period_frame(metric, current_filters)
        previous_df = self._metric_period_frame(metric, previous_filters)
        value_column = self._metric_value_column(metric)

        current_total = self._sum_metric_value(current_df, value_column)
        previous_total = self._sum_metric_value(previous_df, value_column)
        total_change = current_total - previous_total

        current_grouped = self._aggregate_dimension_snapshot(current_df, dimension, value_column)
        previous_grouped = self._aggregate_dimension_snapshot(previous_df, dimension, value_column)
        join_keys = self._dimension_join_keys(dimension)
        merged = current_grouped.merge(previous_grouped, on=join_keys, how="outer", suffixes=("_current", "_previous"))
        merged = merged.fillna({f"{value_column}_current": 0.0, f"{value_column}_previous": 0.0})

        contributors: list[dict[str, Any]] = []
        for _, row in merged.iterrows():
            current_value = float(row.get(f"{value_column}_current") or 0.0)
            previous_value = float(row.get(f"{value_column}_previous") or 0.0)
            change = current_value - previous_value
            change_pct = self._safe_ratio(change, previous_value)
            contribution_pct = self._safe_ratio(change, total_change)
            contributors.append(
                {
                    "name": self._dimension_row_name(row, dimension),
                    "platform": row.get(COL_PLATFORM) if dimension == "platform" else None,
                    "group_code": str(row.get(COL_GROUP_CODE)) if dimension == "business_group" and pd.notna(row.get(COL_GROUP_CODE)) else None,
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "change": change,
                    "change_pct": change_pct,
                    "contribution_pct": contribution_pct,
                    "direction": "positive" if change > 0 else ("negative" if change < 0 else "flat"),
                }
            )

        contributors = sorted(contributors, key=lambda item: abs(float(item.get("change") or 0.0)), reverse=True)[:top_n]
        result = {
            "month": current_month,
            "previous_month": previous_month,
            "metric": metric,
            "dimension": dimension,
            "total_current": current_total,
            "total_previous": previous_total,
            "total_change": total_change,
            "contributors": contributors,
        }
        logger.info("Completed tool get_contribution_analysis with contributors=%s", len(contributors))
        return result

    def get_inventory_turnover_proxy(
        self,
        filters: QueryFilters | None = None,
        top_n: int = 5,
        entity_dimension: str = "business_group",
        parent_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_inventory_turnover_proxy top_n=%s", top_n)
        filters = filters or QueryFilters()
        if not getattr(self.context.artifacts, "revenue_inventory_aligned", pd.DataFrame()).empty:
            dimension = self._normalize_entity_dimension(entity_dimension)
            snapshot = self.get_entity_performance_snapshot(
                entity_dimension=dimension,
                month=filters.month,
                parent_filter=parent_filter,
                filters=filters,
            )
            rows = []
            for row in snapshot.get("rows", []):
                comparable, reason = self._inventory_proxy_comparability(row.get("revenue"), row.get("inventory_amount"))
                efficiency_level = self._efficiency_level(row.get("revenue_inventory_amount_ratio"), is_comparable=comparable)
                rows.append(
                    {
                        "month": row.get("month"),
                        "platform": row.get("platform") or row.get("business_group") or row.get("entity_value"),
                        "group_code": row.get("group_code") or row.get("business_group"),
                        "business_group": row.get("business_group"),
                        "product_line_5": row.get("product_line_5"),
                        "entity_dimension": dimension,
                        "entity_label": snapshot.get("entity_label"),
                        "entity_value": row.get("entity_value"),
                        "revenue": row.get("revenue"),
                        "inventory_amount": row.get("inventory_amount"),
                        "inventory_qty": row.get("inventory_qty"),
                        "revenue_inventory_amount_ratio": row.get("revenue_inventory_amount_ratio"),
                        "revenue_inventory_qty_ratio": row.get("revenue_inventory_qty_ratio"),
                        "proxy_formula": "revenue / inventory_amount",
                        "proxy_numerator": "revenue",
                        "proxy_denominator": "inventory_amount",
                        "proxy_unit": "ratio",
                        "is_comparable": comparable,
                        "non_comparable_reason": reason,
                        "efficiency_level": efficiency_level,
                        "risk_label": self._inventory_proxy_risk_label(efficiency_level),
                        "limitation": "此為營收相對庫存 proxy，非正式周轉指標；revenue<=0 或 inventory_amount<=0 時不列入正常效率排名。",
                    }
                )
            rows = sorted(
                rows,
                key=lambda item: (
                    self._efficiency_sort_order(item.get("efficiency_level")),
                    float(item.get("revenue_inventory_amount_ratio")) if item.get("revenue_inventory_amount_ratio") is not None else float("inf"),
                ),
            )
            return rows[:top_n]
        current_month = filters.month or self._latest_month_for_metric("revenue", filters)
        if current_month is None:
            logger.info("Completed tool get_inventory_turnover_proxy with rows=0 due to missing month")
            return []

        scoped_filters = QueryFilters(
            month=current_month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        df = self.get_metric_table("platform_monthly", scoped_filters).copy()
        if df.empty:
            logger.info("Completed tool get_inventory_turnover_proxy with rows=0")
            return []

        results: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            amount_ratio = row.get(COL_REVENUE_INV_AMOUNT_RATIO)
            qty_ratio = row.get(COL_REVENUE_INV_QTY_RATIO)
            comparable, reason = self._inventory_proxy_comparability(row.get(COL_REVENUE), row.get(COL_INV_AMOUNT))
            efficiency_level = self._efficiency_level(amount_ratio, is_comparable=comparable)
            results.append(
                {
                    "month": row.get(COL_MONTH),
                    "platform": row.get(COL_PLATFORM),
                    "group_code": str(row.get(COL_GROUP_CODE)) if pd.notna(row.get(COL_GROUP_CODE)) else None,
                    "revenue": self._normalize_number(row.get(COL_REVENUE)),
                    "inventory_amount": self._normalize_number(row.get(COL_INV_AMOUNT)),
                    "inventory_qty": self._normalize_number(row.get(COL_INV_QTY)),
                    "revenue_inventory_amount_ratio": self._normalize_number(amount_ratio),
                    "revenue_inventory_qty_ratio": self._normalize_number(qty_ratio),
                    "proxy_formula": "revenue / inventory_amount",
                    "proxy_numerator": "revenue",
                    "proxy_denominator": "inventory_amount",
                    "proxy_unit": "ratio",
                    "is_comparable": comparable,
                    "non_comparable_reason": reason,
                    "efficiency_level": efficiency_level,
                    "risk_label": self._inventory_proxy_risk_label(efficiency_level),
                    "limitation": "此為營收與庫存資料推導的 proxy，非正式周轉指標；revenue<=0 或 inventory_amount<=0 時不列入正常效率排名。",
                }
            )

        results = sorted(
            results,
            key=lambda item: (
                self._efficiency_sort_order(item.get("efficiency_level")),
                float(item.get("revenue_inventory_amount_ratio")) if item.get("revenue_inventory_amount_ratio") is not None else float("inf"),
            ),
        )
        result = results[:top_n]
        logger.info("Completed tool get_inventory_turnover_proxy with rows=%s", len(result))
        return result

    def get_platform_performance_snapshot(
        self,
        filters: QueryFilters | None = None,
        month: str | None = None,
        top_n: int | None = None,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_platform_performance_snapshot month=%s top_n=%s", month, top_n)
        filters = filters or QueryFilters()
        if not getattr(self.context.artifacts, "revenue_inventory_aligned", pd.DataFrame()).empty:
            return self.get_entity_performance_snapshot(
                entity_dimension="business_group",
                month=month,
                filters=filters,
                top_n=top_n,
            )
        effective_filters = QueryFilters(
            month=month or filters.month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        current_month = effective_filters.month or self._latest_month_for_metric("revenue", effective_filters)
        limitations = [
            "此為 deterministic 新事業群 performance scorecard，仍未納入毛利、訂單、出貨、價格與客戶結構。",
            "營收/庫存效率為 proxy，非正式周轉指標。",
        ]
        rubric = {
            "revenue_scale_weight": 0.30,
            "revenue_momentum_weight": 0.20,
            "inventory_efficiency_weight": 0.35,
            "anomaly_score_weight": 0.15,
        }
        if current_month is None:
            limitations.append("目前沒有可用月份，無法產生新事業群 performance snapshot。")
            return {
                "month": None,
                "dimension": "platform",
                "rows": [],
                "summary": {},
                "rubric": rubric,
                "limitations": limitations,
            }

        current_filters = QueryFilters(
            month=current_month,
            platform=effective_filters.platform,
            group_code=effective_filters.group_code,
        )
        current_df = self.get_metric_table("platform_monthly", current_filters).copy()
        if current_df.empty:
            limitations.append("指定月份沒有新事業群層營收與庫存對齊資料。")
            return {
                "month": current_month,
                "dimension": "platform",
                "rows": [],
                "summary": {},
                "rubric": rubric,
                "limitations": limitations,
            }

        current_grouped = self._platform_snapshot_frame(current_df)
        previous_month = self._previous_month_for_snapshot(current_month, effective_filters)
        previous_revenue_by_platform: dict[str, float] = {}
        if previous_month:
            previous_filters = QueryFilters(
                month=previous_month,
                platform=effective_filters.platform,
                group_code=effective_filters.group_code,
            )
            previous_df = self.get_metric_table("platform_monthly", previous_filters).copy()
            if not previous_df.empty:
                previous_grouped = self._platform_snapshot_frame(previous_df)
                previous_revenue_by_platform = {
                    str(row[COL_PLATFORM]): float(row[COL_REVENUE])
                    for _, row in previous_grouped.iterrows()
                    if pd.notna(row.get(COL_REVENUE))
                }
        else:
            limitations.append("缺少前期月份，營收動能分數未納入 health_score。")

        anomaly_counts = self._platform_anomaly_counts(current_filters)
        current_grouped = current_grouped.sort_values(COL_PLATFORM).reset_index(drop=True)
        revenue_values = [self._normalize_number(value) for value in current_grouped[COL_REVENUE].tolist()]
        ratio_values = [self._normalize_number(value) for value in current_grouped[COL_REVENUE_INV_AMOUNT_RATIO].tolist()]
        momentum_values: list[float | None] = []
        base_rows: list[dict[str, Any]] = []

        for _, row in current_grouped.iterrows():
            platform = str(row.get(COL_PLATFORM))
            revenue = self._normalize_number(row.get(COL_REVENUE))
            inventory_amount = self._normalize_number(row.get(COL_INV_AMOUNT))
            inventory_qty = self._normalize_number(row.get(COL_INV_QTY))
            ratio = self._normalize_number(row.get(COL_REVENUE_INV_AMOUNT_RATIO))
            previous_revenue = previous_revenue_by_platform.get(platform)
            mom_change = None
            mom_change_pct = None
            if revenue is not None and previous_revenue is not None:
                mom_change = float(revenue) - float(previous_revenue)
                mom_change_pct = mom_change / float(previous_revenue) if previous_revenue else None
            momentum_values.append(mom_change)
            base_rows.append(
                {
                    "month": current_month,
                    "platform": platform,
                    "revenue": revenue,
                    "inventory_amount": inventory_amount,
                    "inventory_qty": inventory_qty,
                    "revenue_inventory_amount_ratio": ratio,
                    "revenue_mom_change": mom_change,
                    "revenue_mom_change_pct": mom_change_pct,
                    "anomaly_count": anomaly_counts.get(platform, 0),
                }
            )

        if not any(value is not None for value in momentum_values):
            limitations.append("缺少可比較的前期新事業群營收資料，營收動能分數未納入 health_score。")

        revenue_score_map = self._score_by_platform(base_rows, "revenue", higher_is_better=True)
        momentum_score_map = self._score_by_platform(base_rows, "revenue_mom_change", higher_is_better=True)
        efficiency_score_map = self._score_by_platform(base_rows, "revenue_inventory_amount_ratio", higher_is_better=True)
        anomaly_score_map = {
            row["platform"]: max(0.0, 1.0 - min(float(row["anomaly_count"]), 3.0) / 3.0)
            for row in base_rows
        }

        revenue_rank_map = self._rank_by_platform(base_rows, "revenue", descending=True)
        inventory_rank_map = self._rank_by_platform(base_rows, "inventory_amount", descending=True)
        efficiency_rank_map = self._rank_by_platform(base_rows, "revenue_inventory_amount_ratio", descending=True)

        rows: list[dict[str, Any]] = []
        for row in base_rows:
            platform = row["platform"]
            component_scores = {
                "revenue_scale_score": revenue_score_map.get(platform),
                "revenue_momentum_score": momentum_score_map.get(platform),
                "inventory_efficiency_score": efficiency_score_map.get(platform),
                "anomaly_score": anomaly_score_map.get(platform),
            }
            health_score = self._weighted_health_score(component_scores, rubric)
            risk_score = round(1.0 - health_score, 4) if health_score is not None else None
            row.update(
                {
                    "revenue_rank": revenue_rank_map.get(platform),
                    "inventory_rank": inventory_rank_map.get(platform),
                    "efficiency_rank": efficiency_rank_map.get(platform),
                    **component_scores,
                }
            )
            row.update(
                {
                    "health_score": health_score,
                    "risk_score": risk_score,
                    "performance_label": self._performance_label(health_score),
                    "primary_strength": self._platform_primary_strength(row, component_scores),
                    "primary_risk": self._platform_primary_risk(row, component_scores),
                }
            )
            rows.append(row)

        rows = sorted(rows, key=lambda item: (item.get("health_score") is None, -(item.get("health_score") or 0.0), item.get("platform") or ""))
        if top_n is not None:
            rows = rows[: max(int(top_n), 0)]

        summary = self._platform_snapshot_summary(rows)
        result = {
            "month": current_month,
            "dimension": "platform",
            "rows": rows,
            "summary": summary,
            "rubric": rubric,
            "limitations": list(dict.fromkeys(limitations)),
        }
        logger.info("Completed tool get_platform_performance_snapshot with rows=%s", len(rows))
        return result

    def get_period_pair_metric_comparison(
        self,
        metric: str,
        period_a: str,
        period_b: str,
        dimension: str = "overall",
        filters: QueryFilters | None = None,
        top_n: int = 5,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info(
            "Running tool get_period_pair_metric_comparison metric=%s period_a=%s period_b=%s dimension=%s",
            metric,
            period_a,
            period_b,
            dimension,
        )
        filters = filters or QueryFilters()
        metric_column = {
            "revenue": COL_REVENUE,
            "inventory_amount": COL_INV_AMOUNT,
            "inventory_qty": COL_INV_QTY,
        }.get(metric)
        if metric_column is None:
            return {
                "metric": metric,
                "period_a": period_a,
                "period_b": period_b,
                "dimension": dimension,
                "overall": {},
                "breakdown": [],
                "limitations": [f"Unsupported metric: {metric}"],
            }

        source = self._period_pair_source(metric, dimension)
        source = self._apply_filters(source, QueryFilters(platform=filters.platform, group_code=filters.group_code))
        limitations: list[str] = []
        if source.empty:
            limitations.append("目前沒有可用資料可比較這兩個月份。")
            return {
                "metric": metric,
                "period_a": period_a,
                "period_b": period_b,
                "dimension": dimension,
                "overall": {},
                "breakdown": [],
                "limitations": limitations,
            }

        overall = self._period_pair_values(source, metric_column, period_a, period_b)
        if not overall:
            limitations.append("其中一個指定月份沒有可用資料，因此無法計算完整差異。")

        breakdown: list[dict[str, Any]] = []
        dimension_column = {
            "platform": COL_PLATFORM,
            "business_group": COL_GROUP_CODE,
        }.get(dimension)
        if dimension_column and dimension_column in source.columns:
            grouped = (
                source[source[COL_MONTH].isin([period_a, period_b])]
                .groupby([COL_MONTH, dimension_column], dropna=False)[metric_column]
                .sum()
                .reset_index()
            )
            names = sorted(str(value) for value in grouped[dimension_column].dropna().unique().tolist())
            for name in names:
                subset = grouped[grouped[dimension_column].astype(str) == name]
                values = self._period_pair_values(subset, metric_column, period_a, period_b)
                if values:
                    breakdown.append({"name": name, **values})
            breakdown = sorted(breakdown, key=lambda item: abs(float(item.get("change") or 0.0)), reverse=True)[:top_n]

        result = {
            "metric": metric,
            "period_a": period_a,
            "period_b": period_b,
            "dimension": dimension,
            "overall": overall,
            "breakdown": breakdown,
            "limitations": limitations,
        }
        logger.info("Completed tool get_period_pair_metric_comparison with rows=%s", len(breakdown))
        return result

    def _period_pair_source(self, metric: str, dimension: str) -> pd.DataFrame:
        if dimension == "platform":
            return self.context.artifacts.platform_monthly_analysis.copy()
        if dimension == "business_group":
            if metric == "revenue":
                return self.context.artifacts.revenue_enriched.copy()
            return self.context.artifacts.inventory_enriched.copy()
        if metric == "revenue":
            return self.context.artifacts.monthly_revenue.copy()
        if metric == "inventory_amount":
            return self.context.artifacts.monthly_inventory_amount.copy()
        if metric == "inventory_qty":
            return self.context.artifacts.monthly_inventory_qty.copy()
        return pd.DataFrame()

    @staticmethod
    def _period_pair_values(df: pd.DataFrame, metric_column: str, period_a: str, period_b: str) -> dict[str, Any]:
        if df.empty or COL_MONTH not in df.columns or metric_column not in df.columns:
            return {}
        by_month = df.groupby(COL_MONTH)[metric_column].sum()
        if period_a not in by_month.index or period_b not in by_month.index:
            return {}
        value_a = float(by_month.loc[period_a])
        value_b = float(by_month.loc[period_b])
        change = value_b - value_a
        change_pct = change / value_a if value_a else None
        if change > 0:
            direction = "up"
        elif change < 0:
            direction = "down"
        else:
            direction = "flat"
        return {
            "value_a": round(value_a, 2),
            "value_b": round(value_b, 2),
            "change": round(change, 2),
            "change_pct": change_pct,
            "direction": direction,
        }

    @staticmethod
    def _canonical_metric_spec(metric: str) -> tuple[str, str]:
        mapping = {
            "revenue": ("revenue_amount", "營收"),
            "revenue_amount": ("revenue_amount", "營收"),
            "inventory": ("inventory_amount", "庫存金額"),
            "inventory_amount": ("inventory_amount", "庫存金額"),
            "inventory_qty": ("inventory_qty", "庫存數量"),
            "qty": ("inventory_qty", "庫存數量"),
            "revenue_inventory_amount_ratio": ("revenue_inventory_amount_ratio", "營收相對庫存效率"),
            "ratio": ("revenue_inventory_amount_ratio", "營收相對庫存效率"),
            "health_score": ("health_score", "health_score"),
            "risk_score": ("risk_score", "risk_score"),
        }
        return mapping.get(str(metric), ("revenue_amount", "營收"))

    @staticmethod
    def _metric_value_column_from_canonical(metric: str) -> str:
        return {
            "revenue_amount": COL_REVENUE,
            "inventory_amount": COL_INV_AMOUNT,
            "inventory_qty": COL_INV_QTY,
        }.get(metric, COL_REVENUE)

    def _overall_metric_frame(self, metric: str) -> pd.DataFrame:
        if metric == "revenue_amount":
            frame = self.context.artifacts.monthly_revenue.copy()
            return frame.rename(columns={"月份": COL_MONTH})
        if metric == "inventory_amount":
            frame = self.context.artifacts.monthly_inventory_amount.copy()
            return frame.rename(columns={"月份": COL_MONTH})
        if metric == "inventory_qty":
            frame = self.context.artifacts.monthly_inventory_qty.copy()
            return frame.rename(columns={"月份": COL_MONTH})
        return pd.DataFrame()

    @staticmethod
    def _apply_month_window(
        df: pd.DataFrame,
        *,
        recent_n: int | None,
        start_month: str | None,
        end_month: str | None,
        month_column: str = "month_key",
    ) -> pd.DataFrame:
        if df.empty or month_column not in df.columns:
            return df
        scoped = df.copy()
        scoped[month_column] = scoped[month_column].astype(str)
        if start_month:
            scoped = scoped[scoped[month_column] >= str(start_month)]
        if end_month:
            scoped = scoped[scoped[month_column] <= str(end_month)]
        months = sorted(scoped[month_column].dropna().unique().tolist())
        if recent_n is not None and recent_n > 0 and months:
            keep = set(months[-recent_n:])
            scoped = scoped[scoped[month_column].isin(keep)]
        return scoped.reset_index(drop=True)

    def _aligned_metric_value_for_month(
        self,
        df: pd.DataFrame,
        metric: str,
        *,
        group_dimension: str | None = None,
    ) -> pd.DataFrame:
        group_keys = ["month_key"]
        if group_dimension:
            group_keys.append(group_dimension)
        if metric == "revenue_amount":
            grouped = df.groupby(group_keys, dropna=False)["revenue_amount"].sum(min_count=1).reset_index()
            return grouped.rename(columns={"month_key": "month", "revenue_amount": "value"})
        if metric == "inventory_amount":
            grouped = df.groupby(group_keys, dropna=False)["inventory_amount"].sum(min_count=1).reset_index()
            return grouped.rename(columns={"month_key": "month", "inventory_amount": "value"})
        if metric == "inventory_qty":
            grouped = df.groupby(group_keys, dropna=False)["inventory_qty"].sum(min_count=1).reset_index()
            return grouped.rename(columns={"month_key": "month", "inventory_qty": "value"})
        if metric == "revenue_inventory_amount_ratio":
            rows: list[dict[str, Any]] = []
            for keys, subset in df.groupby(group_keys, dropna=False):
                month = keys[0] if isinstance(keys, tuple) else keys
                dimension_value = keys[1] if isinstance(keys, tuple) and len(keys) > 1 else None
                both = subset[subset["data_presence_flag"] == "both"]
                revenue = both["revenue_amount"].sum(min_count=1) if not both.empty else None
                inventory = both["inventory_amount"].sum(min_count=1) if not both.empty else None
                ratio = float(revenue) / float(inventory) if pd.notna(revenue) and pd.notna(inventory) and float(inventory) != 0 else None
                row = {"month": str(month), "value": self._normalize_number(ratio)}
                if group_dimension:
                    row[group_dimension] = dimension_value
                rows.append(row)
            return pd.DataFrame(rows)
        return pd.DataFrame(columns=["month", "value"])

    def _build_entity_series_rows(self, df: pd.DataFrame, metric: str) -> list[dict[str, Any]]:
        month_frame = self._aligned_metric_value_for_month(df, metric)
        return self._series_rows_from_month_frame(month_frame, value_column="value")

    def _series_rows_from_month_frame(self, df: pd.DataFrame, value_column: str) -> list[dict[str, Any]]:
        if df.empty or "month" not in df.columns:
            return []
        ordered = df.sort_values("month").reset_index(drop=True)
        rows: list[dict[str, Any]] = []
        previous_value: float | None = None
        for _, row in ordered.iterrows():
            value = self._normalize_number(row.get(value_column))
            mom_change = None if previous_value is None or value is None else round(float(value) - float(previous_value), 2)
            mom_change_pct = self._safe_ratio(mom_change, previous_value) if mom_change is not None else None
            rows.append(
                {
                    "month": str(row.get("month")),
                    "value": value,
                    "mom_change": mom_change,
                    "mom_change_pct": mom_change_pct,
                }
            )
            previous_value = value
        return rows

    @staticmethod
    def _series_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows:
            return {}
        latest = rows[-1]
        valid_rows = [row for row in rows if row.get("value") is not None]
        if not valid_rows:
            return {"latest_month": latest.get("month"), "latest_value": None}
        first = valid_rows[0]
        peak = max(valid_rows, key=lambda row: float(row.get("value") or 0.0))
        lowest = min(valid_rows, key=lambda row: float(row.get("value") or 0.0))
        overall_change = round(float(latest.get("value") or 0.0) - float(first.get("value") or 0.0), 2)
        return {
            "latest_month": latest.get("month"),
            "latest_value": latest.get("value"),
            "peak_month": peak.get("month"),
            "lowest_month": lowest.get("month"),
            "overall_change": overall_change,
            "overall_change_pct": None if first.get("value") in {None, 0} else overall_change / float(first.get("value")),
            "direction": "up" if overall_change > 0 else ("down" if overall_change < 0 else "flat"),
        }

    @staticmethod
    def _relationship_label(
        revenue_change: float | None,
        inventory_change: float | None,
        ratio_change: float | None,
    ) -> str:
        if ratio_change is not None and ratio_change < 0:
            return "ratio_worsening"
        if revenue_change is None or inventory_change is None:
            return "mixed"
        if revenue_change < 0 and inventory_change > 0:
            return "revenue_down_inventory_up"
        if revenue_change > 0 and inventory_change > 0:
            return "revenue_up_inventory_up"
        if revenue_change == 0 and inventory_change > 0:
            return "revenue_flat_inventory_up"
        if revenue_change > 0 and inventory_change <= 0:
            return "aligned_growth"
        return "mixed"

    def get_root_cause_candidates(
        self,
        filters: QueryFilters | None = None,
        metric: str = "revenue",
        top_n: int = 5,
    ) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_root_cause_candidates metric=%s top_n=%s", metric, top_n)
        filters = filters or QueryFilters()

        if metric != "revenue":
            logger.warning("Unsupported metric for get_root_cause_candidates: %s", metric)
            return {
                "root_cause_available": False,
                "month": filters.month,
                "metric": metric,
                "candidates": [],
                "limitations": [
                    "目前僅支援 revenue 的候選觀察整理。",
                    "目前僅能根據營收、庫存與 mapping 資料整理候選觀察，不能判定根本原因。",
                ],
            }

        breakdown_rows = self.get_yoy_mom_breakdown(filters, metric="revenue", dimension="overall", top_n=1)
        platform_contribution = self.get_contribution_analysis(
            filters,
            metric="revenue",
            dimension="platform",
            top_n=max(top_n, 3),
        )
        group_contribution = self.get_contribution_analysis(
            filters,
            metric="revenue",
            dimension="business_group",
            top_n=max(top_n, 3),
        )
        turnover_rows = self.get_inventory_turnover_proxy(filters, top_n=max(top_n, 3))
        anomaly_rows = self.get_anomalies(filters=filters, top_n=max(top_n, 3))
        ratio_rows = self.get_platform_ratios(filters, top_n=max(top_n, 3))

        month = (
            (breakdown_rows[0].get("month") if breakdown_rows else None)
            or platform_contribution.get("month")
            or group_contribution.get("month")
            or (turnover_rows[0].get("month") if turnover_rows else None)
            or (anomaly_rows[0].get(COL_MONTH) if anomaly_rows else None)
        )

        candidates: list[dict[str, Any]] = []

        top_platform = self._top_contributor(platform_contribution)
        if top_platform:
            platform_match = self._find_matching_turnover(turnover_rows, platform=top_platform.get("platform"))
            anomaly_match = self._find_matching_anomaly(
                anomaly_rows,
                platform=top_platform.get("platform"),
                group_code=top_platform.get("group_code"),
            )
            supporting_tools = ["get_contribution_analysis", "get_yoy_mom_breakdown"]
            if platform_match:
                supporting_tools.append("get_inventory_turnover_proxy")
            if anomaly_match:
                supporting_tools.append("get_anomalies")
            direction = self._candidate_direction(top_platform.get("change"))
            candidates.append(
                {
                    "candidate_type": "platform_contribution",
                    "title": f"{top_platform.get('name')} 是本月營收變化主要貢獻來源",
                    "description": (
                        f"{platform_contribution.get('month')} 相較 {platform_contribution.get('previous_month')}，"
                        f"{top_platform.get('name')} 的營收變動為 {format_number(top_platform.get('change'))}，"
                        f"屬於{self._candidate_direction_label(direction)}方向。"
                    ),
                    "supporting_tools": list(dict.fromkeys(supporting_tools)),
                    "supporting_evidence": {
                        "contribution": top_platform,
                        "breakdown": breakdown_rows[0] if breakdown_rows else None,
                        "turnover_proxy": platform_match,
                        "anomaly": anomaly_match,
                    },
                    "confidence": self._candidate_confidence(supporting_tools),
                    "direction": direction,
                    "recommended_check": "建議進一步檢查該新事業群的訂單、出貨、價格或客戶變化。",
                    "limitation": "目前缺少訂單、出貨、價格、客戶與市場需求資料，不能判定為根本原因。",
                    "_priority_rank": self._candidate_priority(direction),
                    "_magnitude": abs(float(top_platform.get("change") or 0.0)),
                }
            )

        top_group = self._top_contributor(group_contribution)
        if top_group:
            turnover_match = self._find_matching_turnover(turnover_rows, group_code=top_group.get("group_code"))
            anomaly_match = self._find_matching_anomaly(anomaly_rows, group_code=top_group.get("group_code"))
            supporting_tools = ["get_contribution_analysis"]
            if turnover_match:
                supporting_tools.append("get_inventory_turnover_proxy")
            if anomaly_match:
                supporting_tools.append("get_anomalies")
            direction = self._candidate_direction(top_group.get("change"))
            candidates.append(
                {
                    "candidate_type": "business_group_contribution",
                    "title": f"新事業群 {top_group.get('group_code') or top_group.get('name')} 是本月營收變化主要貢獻來源",
                    "description": (
                        f"{group_contribution.get('month')} 相較 {group_contribution.get('previous_month')}，"
                        f"{top_group.get('name')} 的營收變動為 {format_number(top_group.get('change'))}，"
                        f"屬於{self._candidate_direction_label(direction)}方向。"
                    ),
                    "supporting_tools": list(dict.fromkeys(supporting_tools)),
                    "supporting_evidence": {
                        "contribution": top_group,
                        "turnover_proxy": turnover_match,
                        "anomaly": anomaly_match,
                    },
                    "confidence": self._candidate_confidence(supporting_tools),
                    "direction": direction,
                    "recommended_check": "建議進一步檢查該新事業群的近期訂單、出貨或客戶結構變化。",
                    "limitation": "目前缺少訂單、出貨、價格、客戶與市場需求資料，不能判定為根本原因。",
                    "_priority_rank": self._candidate_priority(direction),
                    "_magnitude": abs(float(top_group.get("change") or 0.0)),
                }
            )

        low_efficiency = next((row for row in turnover_rows if row.get("efficiency_level") == "low"), None)
        if low_efficiency:
            anomaly_match = self._find_matching_anomaly(
                anomaly_rows,
                platform=low_efficiency.get("platform"),
                group_code=low_efficiency.get("group_code"),
            )
            supporting_tools = ["get_inventory_turnover_proxy"]
            if anomaly_match:
                supporting_tools.append("get_anomalies")
            if self._find_matching_ratio(
                ratio_rows,
                platform=low_efficiency.get("platform"),
                group_code=low_efficiency.get("group_code"),
            ):
                supporting_tools.append("get_platform_ratios")
            candidates.append(
                {
                    "candidate_type": "inventory_efficiency_pressure",
                    "title": f"{low_efficiency.get('platform')} / 新事業群 {low_efficiency.get('group_code')} 的庫存效率 proxy 偏弱",
                    "description": (
                        f"{low_efficiency.get('month')} 的營收/庫存金額 ratio 為 "
                        f"{format_number(low_efficiency.get('revenue_inventory_amount_ratio'))}，"
                        f"效率層級為 {low_efficiency.get('efficiency_level')}。"
                    ),
                    "supporting_tools": list(dict.fromkeys(supporting_tools)),
                    "supporting_evidence": {
                        "turnover_proxy": low_efficiency,
                        "anomaly": anomaly_match,
                    },
                    "confidence": self._candidate_confidence(supporting_tools),
                    "direction": "negative",
                    "recommended_check": "建議進一步檢查該新事業群的庫存結構、出貨節奏與近期營收變化。",
                    "limitation": "目前缺少訂單、出貨、價格、客戶與市場需求資料，不能判定為根本原因。",
                    "_priority_rank": self._candidate_priority("negative"),
                    "_magnitude": self._candidate_signal_magnitude(
                        low_efficiency.get("revenue_inventory_amount_ratio"),
                        invert=True,
                    ),
                }
            )

        strongest_anomaly = anomaly_rows[0] if anomaly_rows else None
        if strongest_anomaly:
            ratio_match = self._find_matching_ratio(
                ratio_rows,
                platform=strongest_anomaly.get(COL_PLATFORM),
                group_code=strongest_anomaly.get(COL_GROUP_CODE),
            )
            supporting_tools = ["get_anomalies"]
            if ratio_match:
                supporting_tools.append("get_platform_ratios")
            if self._find_matching_turnover(
                turnover_rows,
                platform=strongest_anomaly.get(COL_PLATFORM),
                group_code=strongest_anomaly.get(COL_GROUP_CODE),
            ):
                supporting_tools.append("get_inventory_turnover_proxy")
            candidates.append(
                {
                    "candidate_type": "anomaly_signal",
                    "title": f"{strongest_anomaly.get(COL_PLATFORM, 'N/A')} / 新事業群 {strongest_anomaly.get(COL_GROUP_CODE, 'N/A')} 出現風險訊號",
                    "description": (
                        f"{strongest_anomaly.get(COL_MONTH, 'N/A')} 出現 "
                        f"{strongest_anomaly.get(COL_ANOMALY_TYPE, '異常訊號')}，"
                        f"訊號值為 {format_number(strongest_anomaly.get(COL_ANOMALY_SIGNAL))}。"
                    ),
                    "supporting_tools": list(dict.fromkeys(supporting_tools)),
                    "supporting_evidence": {
                        "anomaly": strongest_anomaly,
                        "platform_ratio": ratio_match,
                    },
                    "confidence": self._candidate_confidence(supporting_tools),
                    "direction": "negative",
                    "recommended_check": "建議進一步檢查該新事業群的近期營收、庫存與出貨節奏是否出現背離。",
                    "limitation": "目前缺少訂單、出貨、價格、客戶與市場需求資料，不能判定為根本原因。",
                    "_priority_rank": self._candidate_priority("negative"),
                    "_magnitude": abs(float(strongest_anomaly.get(COL_ANOMALY_SIGNAL) or 0.0)),
                }
            )

        candidates = sorted(
            candidates,
            key=lambda item: (
                int(item.get("_priority_rank", 3)),
                -float(item.get("_magnitude", 0.0)),
                0 if item.get("confidence") == "medium" else 1,
            ),
        )[:top_n]
        for candidate in candidates:
            candidate.pop("_priority_rank", None)
            candidate.pop("_magnitude", None)

        result = {
            "root_cause_available": False,
            "month": month,
            "metric": metric,
            "candidates": candidates,
            "limitations": [
                "目前僅能根據營收、庫存與 mapping 資料整理候選觀察，不能判定根本原因。",
                "若要確認原因，需要補充訂單、出貨、價格、客戶或市場需求資料。",
            ],
        }
        logger.info("Completed tool get_root_cause_candidates with candidates=%s", len(candidates))
        return result

    def get_anomalies(self, top_n: int = 5, filters: QueryFilters | None = None) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_anomalies")
        df = self.get_metric_table("anomalies", filters)
        results = df.head(top_n).to_dict(orient="records") if not df.empty else []
        logger.info("Completed tool get_anomalies with rows=%s", len(results))
        return results

    def get_correlations(self, top_n: int = 5) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_correlations")
        df = self.get_metric_table("correlations")
        if df.empty:
            return []

        sort_column = COL_CORR_VALUE
        if sort_column in df.columns:
            df = df.assign(_abs_corr=df[sort_column].abs()).sort_values("_abs_corr", ascending=False)
        results = df.head(top_n).drop(columns=["_abs_corr"], errors="ignore").to_dict(orient="records")
        logger.info("Completed tool get_correlations with rows=%s", len(results))
        return results

    def get_mapping_summary(self) -> dict[str, Any]:
        """回傳 data-source/entity alignment metadata。

        名稱因既有 API/Agent compatibility 保留；本方法不讀取 mapping.xlsx，
        內容來自 inventory/revenue 衍生的 normalized entity metadata。
        """
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_mapping_summary")
        mapping = self.context.parsed_mapping
        result = {
            "mapping_success": mapping.mapping_success,
            "business_groups": mapping.business_group_mapping.to_dict(orient="records"),
            "inventory_hqbu_mapping_count": len(mapping.inventory_hqbu_mapping),
            "revenue_platform_mapping_count": len(mapping.revenue_platform_mapping),
            "bridge_candidate_count": len(mapping.bridge_candidates),
        }
        logger.info("Completed tool get_mapping_summary")
        return result

    def get_chart_catalog(self) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_chart_catalog")
        catalog: list[dict[str, Any]] = []
        for chart_key, definition in self._CHART_DEFINITIONS.items():
            metric = definition["metric"]
            catalog.append(
                {
                    "chart_key": chart_key,
                    "title": definition["title"],
                    "chart_type": definition["chart_type"],
                    "metric": metric,
                    "available": self._metric_available(metric),
                    "supported_filters": sorted(self._METRIC_FILTER_SUPPORT.get(metric, set())),
                }
            )
        logger.info("Completed tool get_chart_catalog with rows=%s", len(catalog))
        return catalog

    def get_observation_options(self) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_observation_options")

        months = self._collect_months()
        compare_month_pairs = [
            {"current_month": months[index], "compare_month": months[index - 1]}
            for index in range(1, len(months))
        ]

        platform_df = self.context.artifacts.platform_monthly_analysis
        if not platform_df.empty and COL_PLATFORM in platform_df.columns:
            platforms = sorted(platform_df[COL_PLATFORM].dropna().astype(str).unique().tolist())
        else:
            platforms = []

        business_groups = self.context.parsed_mapping.business_group_mapping.copy()
        group_options = []
        if not business_groups.empty:
            for _, row in business_groups.iterrows():
                group_options.append(
                    {
                        "group_code": str(row.get("事業群代碼")),
                        "group_name": str(row.get("事業群名稱")),
                    }
                )

        product_lines = []
        if not platform_df.empty and "product_line_5" in platform_df.columns:
            product_lines = sorted(platform_df["product_line_5"].dropna().astype(str).unique().tolist())

        result = {
            "row_dimensions": [
                {"value": "month", "label": "月份"},
                {"value": "business_group", "label": "事業群"},
                {"value": "product_line_5", "label": "產品線"},
            ],
            "metrics": [
                {"value": "revenue", "label": "營收"},
                {"value": "inventory_amount", "label": "庫存金額"},
                {"value": "inventory_qty", "label": "庫存 QTY"},
            ],
            "compare_modes": [
                {"value": "previous_period", "label": "前一期比較"},
                {"value": "custom_month", "label": "自訂月份比較"},
                {"value": "none", "label": "不比較"},
            ],
            "months": months,
            "compare_month_pairs": compare_month_pairs,
            "platforms": platforms,
            "business_groups": platforms,
            "product_lines": product_lines,
            "groups": group_options,
        }
        logger.info("Completed tool get_observation_options")
        return result

    def get_observation_table(self, request: ObservationRequest | dict[str, Any]) -> dict[str, Any]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_observation_table")
        if isinstance(request, dict):
            request = ObservationRequest(**request)

        months = self._collect_months()
        latest_month = months[-1] if months else None
        current_month = request.current_month or latest_month
        compare_month = request.compare_month
        if request.compare_mode == "previous_period" and current_month and current_month in months:
            current_index = months.index(current_month)
            compare_month = months[current_index - 1] if current_index > 0 else None

        if request.row_dimension == "month":
            result = self._build_month_observation_table(request)
        else:
            result = self._build_dimension_observation_table(request, current_month, compare_month)

        result["selection"] = {
            "row_dimension": request.row_dimension,
            "metric": request.metric,
            "compare_mode": request.compare_mode,
            "current_month": current_month,
            "compare_month": compare_month,
            "platform": request.platform,
            "group_code": request.group_code,
            "product_line_5": request.product_line_5,
        }
        logger.info("Completed tool get_observation_table with rows=%s", len(result.get("rows", [])))
        return result

    def get_chart_payload(
        self,
        chart_key: str,
        filters: QueryFilters | None = None,
        top_n: int = 8,
        chart_type_override: str | None = None,
        include_table: bool = True,
    ) -> dict[str, Any] | None:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_chart_payload for chart_key=%s", chart_key)
        filters = filters or QueryFilters()
        definition = self._CHART_DEFINITIONS.get(chart_key)
        if definition is None:
            logger.warning("Unknown chart key requested: %s", chart_key)
            return None

        metric = definition["metric"]
        if definition.get("entity_dimension") and definition.get("value_column") in {
            "health_score",
            "revenue_inventory_amount_ratio",
            COL_REVENUE_INV_AMOUNT_RATIO,
        }:
            dimension = self._normalize_entity_dimension(str(definition["entity_dimension"]))
            snapshot = self.get_entity_performance_snapshot(
                entity_dimension=dimension,
                month=filters.month,
                filters=filters,
                top_n=top_n,
            )
            rows = snapshot.get("rows", [])
            if not rows:
                return None
            value_column = definition["value_column"]
            ordered = pd.DataFrame(rows)
            ordered = ordered[ordered[value_column].notna()].copy() if value_column in ordered.columns else pd.DataFrame()
            if ordered.empty:
                return None
            ordered = ordered.sort_values(value_column, ascending=bool(definition.get("sort_ascending", False))).head(top_n)
            payload = {
                "chart_key": chart_key,
                "chart_type": definition["chart_type"],
                "title": definition["title"],
                "x_label": definition["x_label"],
                "y_label": definition["y_label"],
                "labels": ordered["entity_value"].astype(str).tolist(),
                "series": [
                    {
                        "name": definition.get("series_name", value_column),
                        "data": [self._normalize_number(value) for value in ordered[value_column].tolist()],
                    }
                ],
                "filters": self._filters_to_dict(filters),
                "table_preview": ordered[
                    ["entity_value", "revenue", "inventory_amount", "revenue_inventory_amount_ratio", "health_score", "performance_label"]
                ].to_dict(orient="records"),
                "base_chart_type": definition["chart_type"],
            }
            requested_chart_type = self._normalize_chart_type(chart_type_override)
            if requested_chart_type and requested_chart_type != payload["chart_type"]:
                payload = self._apply_chart_type_variant(payload, requested_chart_type)
            return payload
        effective_filters = self._normalize_chart_filters(definition, filters)
        df = self.get_metric_table(metric, effective_filters).copy()
        if df.empty:
            logger.warning("Chart %s skipped because filtered metric table is empty.", chart_key)
            return None

        chart_type = definition["chart_type"]
        if chart_key == "platform_ratio_rank":
            payload = self._build_platform_ratio_chart_payload(chart_key, definition, df, effective_filters, top_n)
        elif chart_key == "anomaly_signal_rank":
            payload = self._build_anomaly_chart_payload(chart_key, definition, df, effective_filters, top_n)
        elif chart_type == "line" and definition.get("group_column"):
            payload = self._build_multi_series_chart_payload(chart_key, definition, df, effective_filters)
        elif chart_type == "line":
            payload = self._build_single_series_chart_payload(chart_key, definition, df, effective_filters)
        else:
            payload = self._build_bar_chart_payload(chart_key, definition, df, effective_filters, top_n)

        payload["base_chart_type"] = definition["chart_type"]
        requested_chart_type = self._normalize_chart_type(chart_type_override)
        if requested_chart_type and requested_chart_type != payload["chart_type"]:
            payload = self._apply_chart_type_variant(payload, requested_chart_type)

        if include_table and not payload.get("table_preview"):
            payload["table_preview"] = self._build_table_preview_from_payload(payload, limit=12)

        payload["title"] = self._chart_title_with_filters(
            str(payload.get("title") or definition["title"]),
            chart_key,
            effective_filters,
        )
        logger.info("Completed tool get_chart_payload for chart_key=%s", chart_key)
        return payload

    def get_chart_table(
        self,
        chart_key: str,
        filters: QueryFilters | None = None,
        top_n: int = 12,
        chart_type_override: str | None = None,
    ) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_chart_table for chart_key=%s", chart_key)
        payload = self.get_chart_payload(
            chart_key,
            filters=filters,
            top_n=top_n,
            chart_type_override=chart_type_override,
            include_table=True,
        )
        rows = payload.get("table_preview", []) if payload else []
        logger.info("Completed tool get_chart_table for chart_key=%s with rows=%s", chart_key, len(rows))
        return rows

    def create_chart_image(
        self,
        chart_key: str,
        filters: QueryFilters | None = None,
        top_n: int = 8,
        chart_type_override: str | None = None,
    ) -> dict[str, Any] | None:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool create_chart_image for chart_key=%s", chart_key)
        payload = self.get_chart_payload(
            chart_key,
            filters=filters,
            top_n=top_n,
            chart_type_override=chart_type_override,
            include_table=True,
        )
        if payload is None:
            return None

        effective_filters = QueryFilters(**payload.get("filters", {}))
        output_path = CHART_DIR / self._chart_filename(chart_key, effective_filters, payload.get("chart_type"))
        render_chart_payload(payload, output_path)
        result = {
            "chart_key": chart_key,
            "title": payload["title"],
            "output_path": str(output_path),
            "filters": self._filters_to_dict(effective_filters),
            "chart_type": payload.get("chart_type"),
        }
        logger.info("Completed tool create_chart_image for chart_key=%s path=%s", chart_key, output_path)
        return result

    def _collect_months(self) -> list[str]:
        sources = [
            self.context.artifacts.monthly_revenue,
            self.context.artifacts.monthly_inventory_amount,
            self.context.artifacts.monthly_inventory_qty,
            self.context.revenue_df,
            self.context.inventory_df,
        ]
        months: set[str] = set()
        for df in sources:
            if df.empty:
                continue
            if "月份" in df.columns:
                months.update(df["月份"].dropna().astype(str).tolist())
            elif "month_key" in df.columns:
                months.update(df["month_key"].dropna().astype(str).tolist())
            elif "日期" in df.columns:
                months.update(df["日期"].dropna().astype(str).tolist())
        return sorted(months)

    def _build_revenue_trend(self, filters: QueryFilters) -> pd.DataFrame:
        df = self._apply_filters(
            self.context.artifacts.revenue_enriched,
            QueryFilters(platform=filters.platform, group_code=filters.group_code),
        )
        if df.empty:
            return pd.DataFrame(columns=["月份", "營收", "月增率", "指標"])

        result = (
            df.groupby("月份", as_index=False)["營收"]
            .sum(min_count=1)
            .sort_values("月份")
            .reset_index(drop=True)
        )
        result["月增率"] = result["營收"].pct_change()
        result["指標"] = "revenue_trend"
        return self._apply_filters(result, QueryFilters(month=filters.month))

    def _build_inventory_trend(self, value_column: str, filters: QueryFilters) -> pd.DataFrame:
        df = self._apply_filters(
            self.context.artifacts.inventory_enriched,
            QueryFilters(platform=filters.platform, group_code=filters.group_code),
        )
        if df.empty:
            return pd.DataFrame(columns=["月份", value_column, "月增率", "指標"])

        result = (
            df.groupby("月份", as_index=False)[value_column]
            .sum(min_count=1)
            .sort_values("月份")
            .reset_index(drop=True)
        )
        result["月增率"] = result[value_column].pct_change()
        result["指標"] = f"inventory_{value_column}_trend"
        return self._apply_filters(result, QueryFilters(month=filters.month))

    def _metric_available(self, metric: str) -> bool:
        if metric == "revenue_trend":
            return not self.context.artifacts.revenue_enriched.empty
        if metric in {"inventory_amount_trend", "inventory_qty_trend"}:
            return not self.context.artifacts.inventory_enriched.empty
        metric_mapping = {
            "revenue_monthly": self.context.artifacts.monthly_revenue,
            "inventory_amount_monthly": self.context.artifacts.monthly_inventory_amount,
            "inventory_qty_monthly": self.context.artifacts.monthly_inventory_qty,
            "revenue_by_group": self.context.artifacts.revenue_by_group,
            "inventory_by_group": self.context.artifacts.inventory_by_group,
            "platform_monthly": self.context.artifacts.platform_monthly_analysis,
            "entity_health_score": self.context.artifacts.revenue_inventory_aligned,
            "anomalies": self.context.artifacts.anomalies,
            "correlations": self.context.artifacts.correlation_analysis,
        }
        df = metric_mapping.get(metric)
        return df is not None and not df.empty

    def _unsupported_filters(self, metric: str, filters: QueryFilters) -> list[str]:
        supported_filters = self._METRIC_FILTER_SUPPORT.get(metric)
        if supported_filters is None:
            return []

        requested_filters = []
        if filters.month:
            requested_filters.append("month")
        if filters.platform:
            requested_filters.append("platform")
        if filters.group_code:
            requested_filters.append("group_code")

        return [name for name in requested_filters if name not in supported_filters]

    @staticmethod
    def _empty_metric_frame(metric: str) -> pd.DataFrame:
        known_columns = {
            "revenue_trend": ["月份", "營收", "月增率", "指標"],
            "inventory_amount_trend": ["月份", "金額", "月增率", "指標"],
            "inventory_qty_trend": ["月份", "QTY", "月增率", "指標"],
            "revenue_monthly": ["月份", "營收", "月增率", "指標"],
            "inventory_amount_monthly": ["月份", "金額", "月增率", "指標"],
            "inventory_qty_monthly": ["月份", "QTY", "月增率", "指標"],
            "revenue_by_group": ["新事業群", "事業群名稱", "營收", "占比", "指標"],
            "inventory_by_group": ["新事業群", "事業群名稱", "金額", "占比", "指標"],
            "platform_monthly": [
                COL_MONTH,
                COL_GROUP_CODE,
                COL_PLATFORM,
                COL_INV_AMOUNT,
                COL_INV_QTY,
                COL_REVENUE,
                COL_REVENUE_INV_AMOUNT_RATIO,
                COL_REVENUE_INV_QTY_RATIO,
            ],
            "anomalies": [
                COL_ANOMALY_TYPE,
                COL_MONTH,
                COL_GROUP_CODE,
                COL_PLATFORM,
                COL_ANOMALY_SIGNAL,
                COL_ANOMALY_REASON,
            ],
            "correlations": [
                COL_CORR_LEVEL,
                COL_CORR_TARGET,
                COL_CORR_METRICS,
                COL_CORR_SAMPLES,
                COL_CORR_VALUE,
                COL_CORR_LABEL,
            ],
        }
        return pd.DataFrame(columns=known_columns.get(metric, []))

    @staticmethod
    def _apply_filters(df: pd.DataFrame, filters: QueryFilters) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        filtered = df.copy()
        if filters.month and "month_key" in filtered.columns:
            filtered = filtered.loc[filtered["month_key"].astype(str) == filters.month]
        if filters.platform and "business_group" in filtered.columns and "平台" not in filtered.columns:
            filtered = filtered.loc[filtered["business_group"].astype(str).str.upper() == filters.platform.upper()]
        if filters.group_code and "business_group" in filtered.columns and "新事業群" not in filtered.columns:
            filtered = filtered.loc[filtered["business_group"].astype(str) == str(filters.group_code)]
        if filters.month:
            if "月份" in filtered.columns:
                filtered = filtered.loc[filtered["月份"].astype(str) == filters.month]
            elif "日期" in filtered.columns:
                filtered = filtered.loc[filtered["日期"].astype(str) == filters.month]

        if filters.platform and "平台" in filtered.columns:
            filtered = filtered.loc[filtered["平台"].astype(str).str.upper() == filters.platform.upper()]

        if filters.group_code:
            if "新事業群" in filtered.columns:
                filtered = filtered.loc[filtered["新事業群"].astype(str) == str(filters.group_code)]
            elif "事業群代碼" in filtered.columns:
                filtered = filtered.loc[filtered["事業群代碼"].astype(str) == str(filters.group_code)]

        return filtered.reset_index(drop=True)

    def _build_single_series_chart_payload(
        self,
        chart_key: str,
        definition: dict[str, Any],
        df: pd.DataFrame,
        filters: QueryFilters,
    ) -> dict[str, Any]:
        label_column = definition.get("label_column", COL_MONTH)
        value_column = definition["value_column"]
        ordered = df.sort_values(label_column).reset_index(drop=True)
        return {
            "chart_key": chart_key,
            "chart_type": definition["chart_type"],
            "title": definition["title"],
            "x_label": definition["x_label"],
            "y_label": definition["y_label"],
            "labels": ordered[label_column].astype(str).tolist(),
            "series": [
                {
                    "name": definition.get("series_name", value_column),
                    "data": [self._normalize_number(value) for value in ordered[value_column].tolist()],
                }
            ],
            "filters": self._filters_to_dict(filters),
            "table_preview": ordered[[label_column, value_column]].rename(
                columns={label_column: "label", value_column: definition.get("series_name", value_column)}
            ).to_dict(orient="records"),
        }

    def _build_multi_series_chart_payload(
        self,
        chart_key: str,
        definition: dict[str, Any],
        df: pd.DataFrame,
        filters: QueryFilters,
    ) -> dict[str, Any]:
        label_column = definition["label_column"]
        group_column = definition["group_column"]
        value_column = definition["value_column"]
        pivot = (
            df.pivot_table(index=label_column, columns=group_column, values=value_column, aggfunc="sum")
            .sort_index()
            .fillna(0)
        )
        return {
            "chart_key": chart_key,
            "chart_type": definition["chart_type"],
            "title": definition["title"],
            "x_label": definition["x_label"],
            "y_label": definition["y_label"],
            "labels": pivot.index.astype(str).tolist(),
            "series": [
                {
                    "name": str(column),
                    "data": [self._normalize_number(value) for value in pivot[column].tolist()],
                }
                for column in pivot.columns
            ],
            "filters": self._filters_to_dict(filters),
            "table_preview": pivot.reset_index().rename(columns={label_column: "label"}).to_dict(orient="records"),
        }

    def _build_bar_chart_payload(
        self,
        chart_key: str,
        definition: dict[str, Any],
        df: pd.DataFrame,
        filters: QueryFilters,
        top_n: int,
    ) -> dict[str, Any]:
        label_column = definition["label_column"]
        value_column = definition["value_column"]
        if label_column in df.columns and value_column in df.columns:
            ordered = (
                df.groupby(label_column, dropna=False, as_index=False)[value_column]
                .sum(min_count=1)
                .sort_values(value_column, ascending=False)
                .head(top_n)
                .reset_index(drop=True)
            )
        else:
            ordered = df.sort_values(value_column, ascending=False).head(top_n).reset_index(drop=True)
        ordered = ordered[ordered[value_column].notna()].head(top_n).reset_index(drop=True)
        return {
            "chart_key": chart_key,
            "chart_type": definition["chart_type"],
            "title": definition["title"],
            "x_label": definition["x_label"],
            "y_label": definition["y_label"],
            "labels": ordered[label_column].fillna("未對應").astype(str).tolist(),
            "series": [
                {
                    "name": definition.get("series_name", value_column),
                    "data": [self._normalize_number(value) for value in ordered[value_column].tolist()],
                }
            ],
            "filters": self._filters_to_dict(filters),
            "table_preview": ordered[[label_column, value_column]].rename(
                columns={label_column: "label", value_column: definition.get("series_name", value_column)}
            ).to_dict(orient="records"),
        }

    def _build_platform_ratio_chart_payload(
        self,
        chart_key: str,
        definition: dict[str, Any],
        df: pd.DataFrame,
        filters: QueryFilters,
        top_n: int,
    ) -> dict[str, Any]:
        ordered = df[df[COL_REVENUE_INV_AMOUNT_RATIO].notna()].sort_values(COL_REVENUE_INV_AMOUNT_RATIO, ascending=True).head(top_n).copy()
        ordered["chart_label"] = ordered.apply(
            lambda row: f"{row.get(COL_MONTH)} / {row.get(COL_PLATFORM) or '未標示新事業群'}",
            axis=1,
        )
        return {
            "chart_key": chart_key,
            "chart_type": definition["chart_type"],
            "title": definition["title"],
            "x_label": definition["x_label"],
            "y_label": definition["y_label"],
            "labels": ordered["chart_label"].tolist(),
            "series": [
                {
                    "name": definition.get("series_name", COL_REVENUE_INV_AMOUNT_RATIO),
                    "data": [self._normalize_number(value) for value in ordered[COL_REVENUE_INV_AMOUNT_RATIO].tolist()],
                }
            ],
            "filters": self._filters_to_dict(filters),
            "table_preview": ordered[
                [COL_MONTH, COL_GROUP_CODE, COL_PLATFORM, COL_REVENUE, COL_INV_AMOUNT, COL_REVENUE_INV_AMOUNT_RATIO]
            ].to_dict(orient="records"),
        }

    def _build_anomaly_chart_payload(
        self,
        chart_key: str,
        definition: dict[str, Any],
        df: pd.DataFrame,
        filters: QueryFilters,
        top_n: int,
    ) -> dict[str, Any]:
        ordered = df.copy()
        ordered["signal_abs"] = ordered[COL_ANOMALY_SIGNAL].abs()
        ordered = ordered.sort_values("signal_abs", ascending=False).head(top_n).reset_index(drop=True)
        ordered["chart_label"] = ordered.apply(
            lambda row: f"{row.get(COL_MONTH)} / {row.get(COL_PLATFORM) or '未標示新事業群'} / {row.get(COL_ANOMALY_TYPE)}",
            axis=1,
        )
        preview_columns = [
            column
            for column in [COL_MONTH, COL_GROUP_CODE, COL_PLATFORM, COL_ANOMALY_TYPE, COL_ANOMALY_SIGNAL]
            if column in ordered.columns
        ]
        reason_column = None
        for candidate in [COL_ANOMALY_REASON, "??", "??"]:
            if candidate in ordered.columns:
                reason_column = candidate
                break
        if reason_column and reason_column not in preview_columns:
            preview_columns.append(reason_column)

        return {
            "chart_key": chart_key,
            "chart_type": definition["chart_type"],
            "title": definition["title"],
            "x_label": definition["x_label"],
            "y_label": definition["y_label"],
            "labels": ordered["chart_label"].tolist(),
            "series": [
                {
                    "name": definition.get("series_name", COL_ANOMALY_SIGNAL),
                    "data": [self._normalize_number(value) for value in ordered["signal_abs"].tolist()],
                }
            ],
            "filters": self._filters_to_dict(filters),
            "table_preview": ordered[preview_columns].to_dict(orient="records"),
        }

    def _platform_snapshot_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        grouped = (
            df.groupby(COL_PLATFORM, dropna=False, as_index=False)
            .agg({COL_REVENUE: "sum", COL_INV_AMOUNT: "sum", COL_INV_QTY: "sum"})
            .reset_index(drop=True)
        )
        grouped[COL_REVENUE_INV_AMOUNT_RATIO] = grouped.apply(
            lambda row: (
                float(row[COL_REVENUE]) / float(row[COL_INV_AMOUNT])
                if pd.notna(row.get(COL_REVENUE)) and pd.notna(row.get(COL_INV_AMOUNT)) and float(row[COL_INV_AMOUNT]) != 0
                else None
            ),
            axis=1,
        )
        return grouped

    def _previous_month_for_snapshot(self, current_month: str, filters: QueryFilters) -> str | None:
        months = self._available_months_for_metric(
            "revenue",
            QueryFilters(platform=filters.platform, group_code=filters.group_code),
        )
        if current_month not in months:
            return None
        index = months.index(current_month)
        return months[index - 1] if index > 0 else None

    def _platform_anomaly_counts(self, filters: QueryFilters) -> dict[str, int]:
        anomalies = self.get_metric_table("anomalies", filters)
        if anomalies.empty or COL_PLATFORM not in anomalies.columns:
            return {}
        counts = anomalies.groupby(COL_PLATFORM, dropna=False).size().to_dict()
        return {str(platform): int(count) for platform, count in counts.items()}

    @staticmethod
    def _score_by_platform(rows: list[dict[str, Any]], value_key: str, *, higher_is_better: bool) -> dict[str, float | None]:
        values = [float(row[value_key]) for row in rows if row.get(value_key) is not None]
        if not values:
            return {str(row["platform"]): None for row in rows}
        min_value = min(values)
        max_value = max(values)
        score_map: dict[str, float | None] = {}
        for row in rows:
            platform = str(row["platform"])
            value = row.get(value_key)
            if value is None:
                score_map[platform] = None
                continue
            if max_value == min_value:
                score = 1.0
            else:
                score = (float(value) - min_value) / (max_value - min_value)
                if not higher_is_better:
                    score = 1.0 - score
            score_map[platform] = round(max(0.0, min(1.0, score)), 4)
        return score_map

    @staticmethod
    def _rank_by_platform(rows: list[dict[str, Any]], value_key: str, *, descending: bool) -> dict[str, int | None]:
        candidates = [row for row in rows if row.get(value_key) is not None]
        ranked = sorted(candidates, key=lambda row: float(row[value_key]), reverse=descending)
        ranks = {str(row["platform"]): index + 1 for index, row in enumerate(ranked)}
        return {str(row["platform"]): ranks.get(str(row["platform"])) for row in rows}

    @staticmethod
    def _weighted_health_score(component_scores: dict[str, float | None], rubric: dict[str, float]) -> float | None:
        mapping = {
            "revenue_scale_score": "revenue_scale_weight",
            "revenue_momentum_score": "revenue_momentum_weight",
            "inventory_efficiency_score": "inventory_efficiency_weight",
            "anomaly_score": "anomaly_score_weight",
        }
        weighted_sum = 0.0
        available_weight = 0.0
        for score_key, weight_key in mapping.items():
            score = component_scores.get(score_key)
            weight = float(rubric.get(weight_key, 0.0))
            if score is None:
                continue
            weighted_sum += float(score) * weight
            available_weight += weight
        if available_weight == 0:
            return None
        return round(weighted_sum / available_weight, 4)

    @staticmethod
    def _performance_label(health_score: float | None) -> str:
        if health_score is None:
            return "insufficient_score"
        if health_score >= 0.75:
            return "healthy_candidate"
        if health_score >= 0.55:
            return "stable_watch"
        if health_score >= 0.35:
            return "watch"
        return "risk_candidate"

    @staticmethod
    def _platform_primary_strength(row: dict[str, Any], component_scores: dict[str, float | None]) -> str:
        strengths: list[str] = []
        if row.get("revenue_rank") == 1:
            strengths.append("營收規模排名較高")
        if row.get("efficiency_rank") == 1:
            strengths.append("營收相對庫存效率 proxy 較高")
        if component_scores.get("anomaly_score") == 1.0:
            strengths.append("目前未見同月異常訊號")
        return "；".join(strengths) if strengths else "綜合分數來自營收規模、動能、效率 proxy 與異常訊號"

    @staticmethod
    def _platform_primary_risk(row: dict[str, Any], component_scores: dict[str, float | None]) -> str:
        risks: list[str] = []
        if row.get("anomaly_count"):
            risks.append(f"同月異常訊號 {row.get('anomaly_count')} 筆")
        if row.get("efficiency_rank") is not None and row.get("efficiency_rank") >= 3:
            risks.append("營收相對庫存效率 proxy 排名偏後")
        if component_scores.get("revenue_momentum_score") is not None and component_scores.get("revenue_momentum_score") <= 0.25:
            risks.append("營收動能相對偏弱")
        return "；".join(risks) if risks else "目前 scorecard 未顯示主要風險訊號"

    @staticmethod
    def _platform_snapshot_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        def best_by(key: str, *, reverse: bool = True) -> str | None:
            candidates = [row for row in rows if row.get(key) is not None]
            if not candidates:
                return None
            return str(sorted(candidates, key=lambda row: float(row[key]), reverse=reverse)[0].get("platform"))

        return {
            "best_platform": best_by("health_score", reverse=True),
            "weakest_platform": best_by("health_score", reverse=False),
            "top_revenue_platform": best_by("revenue", reverse=True),
            "top_inventory_platform": best_by("inventory_amount", reverse=True),
            "highest_efficiency_platform": best_by("revenue_inventory_amount_ratio", reverse=True),
            "lowest_efficiency_platform": best_by("revenue_inventory_amount_ratio", reverse=False),
        }

    def _entity_aligned_frame(
        self,
        dimension: str,
        parent_filter: dict[str, Any] | None,
        filters: QueryFilters,
    ) -> pd.DataFrame:
        df = self.context.artifacts.revenue_inventory_aligned.copy()
        if df.empty:
            return df
        if filters.month and "month_key" in df.columns:
            df = df[df["month_key"].astype(str) == filters.month]
        if filters.platform and "business_group" in df.columns:
            df = df[df["business_group"].astype(str).str.upper() == filters.platform.upper()]
        if filters.group_code and "business_group" in df.columns:
            df = df[df["business_group"].astype(str) == str(filters.group_code)]
        if parent_filter:
            for key, value in parent_filter.items():
                normalized_key = "business_group" if key in {"platform", "group_code"} else key
                if value is not None and normalized_key in df.columns:
                    df = df[df[normalized_key].astype(str) == str(value)]
        return df.reset_index(drop=True)

    def _entity_snapshot_rows(
        self,
        dimension: str,
        month: str,
        parent_filter: dict[str, Any] | None,
        filters: QueryFilters,
    ) -> list[dict[str, Any]]:
        df = self._entity_aligned_frame(dimension, parent_filter, QueryFilters(month=month, platform=filters.platform, group_code=filters.group_code))
        if df.empty or dimension not in df.columns:
            return []

        rows: list[dict[str, Any]] = []
        for entity_value, subset in df.groupby(dimension, dropna=False):
            entity_text = str(entity_value) if pd.notna(entity_value) else "未標示"
            both = subset[subset["data_presence_flag"] == "both"]
            revenue = self._normalize_number(subset["revenue_amount"].sum(min_count=1))
            inventory_amount = self._normalize_number(subset["inventory_amount"].sum(min_count=1))
            inventory_qty = self._normalize_number(subset["inventory_qty"].sum(min_count=1))
            both_revenue = both["revenue_amount"].sum(min_count=1) if not both.empty else None
            both_inventory_amount = both["inventory_amount"].sum(min_count=1) if not both.empty else None
            both_inventory_qty = both["inventory_qty"].sum(min_count=1) if not both.empty else None
            amount_ratio = (
                float(both_revenue) / float(both_inventory_amount)
                if both_inventory_amount is not None
                and pd.notna(both_inventory_amount)
                and float(both_inventory_amount) != 0
                and both_revenue is not None
                and pd.notna(both_revenue)
                else None
            )
            qty_ratio = (
                float(both_revenue) / float(both_inventory_qty)
                if both_inventory_qty is not None
                and pd.notna(both_inventory_qty)
                and float(both_inventory_qty) != 0
                and both_revenue is not None
                and pd.notna(both_revenue)
                else None
            )
            presence_counts = subset["data_presence_flag"].value_counts().to_dict()
            row = {
                "month": month,
                "entity_dimension": dimension,
                "entity_label": ENTITY_LABELS[dimension],
                "entity_value": entity_text,
                "name": entity_text,
                "business_group": entity_text if dimension == "business_group" else None,
                "product_line_5": entity_text if dimension == "product_line_5" else None,
                "platform": entity_text if dimension == "business_group" else None,
                "group_code": entity_text if dimension == "business_group" else None,
                "revenue": revenue,
                "revenue_amount": revenue,
                "inventory_amount": inventory_amount,
                "inventory_qty": inventory_qty,
                "revenue_inventory_amount_ratio": self._normalize_number(amount_ratio),
                "revenue_inventory_qty_ratio": self._normalize_number(qty_ratio),
                "anomaly_count": 0,
                "data_presence_counts": {str(key): int(value) for key, value in presence_counts.items()},
                "both_row_share": self._safe_ratio(float(presence_counts.get("both", 0)), float(len(subset))),
                "row_count": int(len(subset)),
                "limitation": None if presence_counts.get("both") else "此 entity 沒有 revenue/inventory 同時存在的 grain，未計算 ratio。",
            }
            if dimension == "product_line_5":
                groups = sorted(subset["business_group"].dropna().astype(str).unique().tolist())
                row["business_groups"] = groups
                if parent_filter and parent_filter.get("business_group"):
                    row["business_group"] = str(parent_filter["business_group"])
                    row["parent_business_group"] = str(parent_filter["business_group"])
            rows.append(row)
        return rows

    def _latest_common_month(self) -> str | None:
        report = getattr(self.context.artifacts, "data_quality_report", {}) or getattr(self.context, "real_data_quality_report", {}) or {}
        if report.get("latest_common_month"):
            return report["latest_common_month"]
        df = self.context.artifacts.revenue_inventory_aligned
        if df.empty or "month_key" not in df.columns:
            return None
        both = df[df.get("data_presence_flag") == "both"]
        source = both if not both.empty else df
        months = sorted(source["month_key"].dropna().astype(str).unique().tolist())
        return months[-1] if months else None

    def _previous_common_month(
        self,
        current_month: str,
        dimension: str,
        parent_filter: dict[str, Any] | None,
        filters: QueryFilters,
    ) -> str | None:
        df = self._entity_aligned_frame(dimension, parent_filter, filters)
        if df.empty:
            return None
        both = df[df.get("data_presence_flag") == "both"]
        source = both if not both.empty else df
        months = sorted(source["month_key"].dropna().astype(str).unique().tolist())
        if current_month not in months:
            return None
        index = months.index(current_month)
        return months[index - 1] if index > 0 else None

    @staticmethod
    def _normalize_entity_dimension(entity_dimension: str) -> str:
        normalized = normalize_entity_dimension(entity_dimension)
        if normalized in {"business_group", "product_line_5"}:
            return normalized
        if entity_dimension in {"product_line", "productline_5"}:
            return "product_line_5"
        return "business_group"

    @staticmethod
    def _normalize_entity_ranking_metric(metric: str) -> str:
        normalized = str(metric or "").strip().lower()
        mapping = {
            "revenue": "revenue_amount",
            "sales": "revenue_amount",
            "revenue_amount": "revenue_amount",
            "inventory": "inventory_amount",
            "inventory_amount": "inventory_amount",
            "inventory_qty": "inventory_qty",
            "qty": "inventory_qty",
            "revenue_inventory_ratio": "revenue_inventory_amount_ratio",
            "revenue_inventory_amount_ratio": "revenue_inventory_amount_ratio",
            "ratio": "revenue_inventory_amount_ratio",
            "efficiency": "revenue_inventory_amount_ratio",
            "health": "health_score",
            "health_score": "health_score",
            "risk": "risk_score",
            "risk_score": "risk_score",
        }
        return mapping.get(normalized, "revenue_amount")

    @staticmethod
    def _entity_ranking_metric_label(metric: str) -> str:
        return {
            "revenue_amount": "營收",
            "inventory_amount": "庫存金額",
            "inventory_qty": "庫存 QTY",
            "revenue_inventory_amount_ratio": "營收相對庫存效率 proxy",
            "health_score": "health_score",
            "risk_score": "risk_score",
        }.get(metric, metric)

    @staticmethod
    def _entity_metric_sort_direction(metric: str, requested_direction: str | None = None) -> str:
        if requested_direction in {"ascending", "descending"}:
            return requested_direction
        return "descending"

    @staticmethod
    def _dominant_presence_flag(counts: Any) -> str | None:
        if not isinstance(counts, dict) or not counts:
            return None
        ordered = sorted(counts.items(), key=lambda item: int(item[1] or 0), reverse=True)
        return str(ordered[0][0]) if ordered else None

    @staticmethod
    def _score_by_entity(rows: list[dict[str, Any]], value_key: str, *, higher_is_better: bool) -> dict[str, float | None]:
        values = [float(row[value_key]) for row in rows if row.get(value_key) is not None]
        if not values:
            return {str(row["entity_value"]): None for row in rows}
        min_value = min(values)
        max_value = max(values)
        score_map: dict[str, float | None] = {}
        for row in rows:
            entity = str(row["entity_value"])
            value = row.get(value_key)
            if value is None:
                score_map[entity] = None
                continue
            if max_value == min_value:
                score = 1.0
            else:
                score = (float(value) - min_value) / (max_value - min_value)
                if not higher_is_better:
                    score = 1.0 - score
            score_map[entity] = round(max(0.0, min(1.0, score)), 4)
        return score_map

    @staticmethod
    def _rank_by_entity(rows: list[dict[str, Any]], value_key: str, *, descending: bool) -> dict[str, int | None]:
        candidates = [row for row in rows if row.get(value_key) is not None]
        ranked = sorted(candidates, key=lambda row: float(row[value_key]), reverse=descending)
        ranks = {str(row["entity_value"]): index + 1 for index, row in enumerate(ranked)}
        return {str(row["entity_value"]): ranks.get(str(row["entity_value"])) for row in rows}

    @staticmethod
    def _entity_health_score(component_scores: dict[str, float | None], rubric: dict[str, float]) -> float | None:
        mapping = {
            "revenue_scale_score": "revenue_scale_weight",
            "revenue_momentum_score": "revenue_momentum_weight",
            "inventory_efficiency_score": "inventory_efficiency_weight",
            "data_completeness_score": "data_completeness_weight",
        }
        weighted_sum = 0.0
        available_weight = 0.0
        for score_key, weight_key in mapping.items():
            score = component_scores.get(score_key)
            weight = float(rubric.get(weight_key, 0.0))
            if score is None:
                continue
            weighted_sum += float(score) * weight
            available_weight += weight
        if available_weight == 0:
            return None
        return round(weighted_sum / available_weight, 4)

    @staticmethod
    def _entity_snapshot_summary(rows: list[dict[str, Any]], dimension: str) -> dict[str, Any]:
        def best_by(key: str, *, reverse: bool = True, allow_unmapped: bool = True) -> str | None:
            candidates = [row for row in rows if row.get(key) is not None]
            if not allow_unmapped:
                mapped_candidates = [row for row in candidates if not is_unmapped_entity(row.get("entity_value"))]
                if mapped_candidates:
                    candidates = mapped_candidates
            if not candidates:
                return None
            return str(sorted(candidates, key=lambda row: float(row[key]), reverse=reverse)[0].get("entity_value"))

        best = best_by("health_score", reverse=True, allow_unmapped=False)
        weakest = best_by("health_score", reverse=False)
        summary = {
            "best_entity": best,
            "weakest_entity": weakest,
            "top_revenue_entity": best_by("revenue", reverse=True, allow_unmapped=False),
            "top_inventory_entity": best_by("inventory_amount", reverse=True, allow_unmapped=False),
            "highest_efficiency_entity": best_by("revenue_inventory_amount_ratio", reverse=True, allow_unmapped=False),
            "lowest_efficiency_entity": best_by("revenue_inventory_amount_ratio", reverse=False),
            "unmapped_entity_count": sum(1 for row in rows if is_unmapped_entity(row.get("entity_value"))),
        }
        if dimension == "business_group":
            summary.update(
                {
                    "best_platform": best,
                    "weakest_platform": weakest,
                    "top_revenue_platform": summary["top_revenue_entity"],
                    "top_inventory_platform": summary["top_inventory_entity"],
                }
            )
        return summary

    @staticmethod
    def _entity_primary_strength(row: dict[str, Any], label: str) -> str:
        strengths: list[str] = []
        if row.get("revenue_rank") == 1:
            strengths.append(f"{label}營收規模排名較高")
        if row.get("efficiency_rank") == 1:
            strengths.append("營收相對庫存 proxy 較佳")
        if row.get("both_row_share") == 1:
            strengths.append("資料對齊完整度較高")
        return "；".join(strengths) if strengths else "綜合分數來自營收、庫存 proxy 與資料完整性。"

    @staticmethod
    def _entity_primary_risk(row: dict[str, Any], label: str) -> str:
        risks: list[str] = []
        if row.get("efficiency_rank") is not None and row.get("efficiency_rank") >= 3:
            risks.append("營收相對庫存 proxy 排名偏後")
        if row.get("both_row_share") is not None and row.get("both_row_share") < 1:
            risks.append("存在 revenue_only 或 inventory_only grain")
        if row.get("revenue_mom_change") is not None and row.get("revenue_mom_change") < 0:
            risks.append(f"{label}營收較前期下降")
        return "；".join(risks) if risks else "目前 scorecard 未顯示主要風險訊號。"

    @staticmethod
    def _normalize_number(value: Any) -> float | int | None:
        if pd.isna(value):
            return None
        if isinstance(value, numbers.Real):
            parsed = float(value)
            return int(parsed) if parsed.is_integer() else parsed
        try:
            parsed = float(value)
            return int(parsed) if parsed.is_integer() else parsed
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _filters_to_dict(filters: QueryFilters | None) -> dict[str, Any]:
        if filters is None:
            return {"month": None, "platform": None, "group_code": None}
        return {
            "month": filters.month,
            "platform": filters.platform,
            "group_code": filters.group_code,
        }

    def _chart_filename(self, chart_key: str, filters: QueryFilters | None, chart_type: str | None = None) -> str:
        filters = filters or QueryFilters()
        parts = [chart_key]
        if chart_type:
            parts.append(chart_type)
        if filters.month:
            parts.append(filters.month)
        if filters.platform:
            parts.append(filters.platform)
        if filters.group_code:
            parts.append(f"group-{filters.group_code}")
        safe = "_".join(self._sanitize_filename_part(part) for part in parts if part)
        return f"{safe}.png"

    @staticmethod
    def _sanitize_filename_part(value: str) -> str:
        return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in str(value))

    def _normalize_chart_filters(self, definition: dict[str, Any], filters: QueryFilters | None) -> QueryFilters:
        filters = filters or QueryFilters()
        if not definition.get("default_latest_month") or filters.month:
            return filters

        months = self._collect_months()
        if not months:
            return filters

        return QueryFilters(
            month=months[-1],
            platform=filters.platform,
            group_code=filters.group_code,
        )

    @staticmethod
    def _normalize_chart_type(chart_type: str | None) -> str | None:
        normalized = str(chart_type or "").strip().lower()
        if normalized in {"line", "bar", "pie", "area"}:
            return normalized
        return None

    def _chart_title_with_filters(self, title: str, chart_key: str, filters: QueryFilters | None) -> str:
        filters = filters or QueryFilters()
        if filters.platform:
            if chart_key in {"platform_monthly_revenue", "entity_time_series_line"}:
                return f"{filters.platform} 各月營收趨勢"
            if chart_key == "platform_monthly_inventory_amount":
                return f"{filters.platform} 各月庫存金額趨勢"
            if chart_key == "platform_monthly_inventory_qty":
                return f"{filters.platform} 各月庫存數量趨勢"
        if filters.month and title.startswith("最新月份"):
            title = f"{filters.month} {title[len('最新月份'):]}"
        if chart_key.endswith("_bar") and filters.month and "長條圖" not in title:
            return title.replace("比較", "長條圖") if "比較" in title else f"{title}長條圖"
        return title

    def _metric_config(self, metric: str) -> dict[str, str]:
        config = {
            "revenue": {"column": COL_REVENUE, "label": "營收"},
            "inventory_amount": {"column": COL_INV_AMOUNT, "label": "庫存金額"},
            "inventory_qty": {"column": COL_INV_QTY, "label": "庫存QTY"},
        }
        return config.get(metric, config["revenue"])

    def _tool_has_current_previous_period(self, metric: str) -> bool:
        current_month, previous_month = self._resolve_current_previous_month(metric, QueryFilters())
        return bool(current_month and previous_month)

    def _metric_source_frame(self, metric: str) -> pd.DataFrame:
        if metric == "revenue":
            return self.context.artifacts.revenue_enriched.copy()
        if metric in {"inventory_amount", "inventory_qty"}:
            return self.context.artifacts.inventory_enriched.copy()
        return pd.DataFrame()

    @staticmethod
    def _metric_value_column(metric: str) -> str:
        return {
            "revenue": COL_REVENUE,
            "inventory_amount": COL_INV_AMOUNT,
            "inventory_qty": COL_INV_QTY,
        }.get(metric, COL_REVENUE)

    def _latest_month_for_metric(self, metric: str, filters: QueryFilters) -> str | None:
        base_filters = QueryFilters(platform=filters.platform, group_code=filters.group_code)
        months = self._available_months_for_metric(metric, base_filters)
        return months[-1] if months else None

    def _resolve_current_previous_month(self, metric: str, filters: QueryFilters) -> tuple[str | None, str | None]:
        base_filters = QueryFilters(platform=filters.platform, group_code=filters.group_code)
        months = self._available_months_for_metric(metric, base_filters)
        if not months:
            return None, None

        current_month = filters.month or months[-1]
        if current_month not in months:
            return current_month, None

        current_index = months.index(current_month)
        previous_month = months[current_index - 1] if current_index > 0 else None
        return current_month, previous_month

    def _available_months_for_metric(self, metric: str, filters: QueryFilters) -> list[str]:
        df = self._apply_filters(self._metric_source_frame(metric), filters)
        if df.empty or COL_MONTH not in df.columns:
            return []
        return sorted(df[COL_MONTH].dropna().astype(str).unique().tolist())

    def _metric_period_frame(self, metric: str, filters: QueryFilters) -> pd.DataFrame:
        return self._apply_filters(self._metric_source_frame(metric), filters)

    def _build_period_breakdown_rows(
        self,
        *,
        current_df: pd.DataFrame,
        previous_df: pd.DataFrame,
        yoy_df: pd.DataFrame,
        metric: str,
        dimension: str,
        current_month: str,
        previous_month: str,
        yoy_available: bool,
        yoy_reason: str,
    ) -> list[dict[str, Any]]:
        value_column = self._metric_value_column(metric)
        if dimension == "overall":
            current_value = self._sum_metric_value(current_df, value_column)
            previous_value = self._sum_metric_value(previous_df, value_column)
            yoy_value = self._sum_metric_value(yoy_df, value_column) if yoy_available else None
            mom_change = current_value - previous_value
            mom_change_pct = self._safe_ratio(mom_change, previous_value)
            yoy_change = current_value - yoy_value if yoy_available and yoy_value is not None else None
            yoy_change_pct = self._safe_ratio(yoy_change, yoy_value) if yoy_available and yoy_value is not None else None
            return [
                {
                    "month": current_month,
                    "previous_month": previous_month,
                    "metric": metric,
                    "dimension": dimension,
                    "name": "overall",
                    "platform": None,
                    "group_code": None,
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "mom_change": mom_change,
                    "mom_change_pct": mom_change_pct,
                    "mom_direction": self._change_direction(mom_change),
                    "yoy_available": yoy_available,
                    "yoy_change": yoy_change,
                    "yoy_change_pct": yoy_change_pct,
                    "yoy_reason": yoy_reason,
                    "severity": self._severity_from_pct(mom_change_pct),
                }
            ]

        current_grouped = self._aggregate_dimension_snapshot(current_df, dimension, value_column)
        previous_grouped = self._aggregate_dimension_snapshot(previous_df, dimension, value_column)
        yoy_grouped = self._aggregate_dimension_snapshot(yoy_df, dimension, value_column) if yoy_available else pd.DataFrame()
        join_keys = self._dimension_join_keys(dimension)
        merged = current_grouped.merge(previous_grouped, on=join_keys, how="outer", suffixes=("_current", "_previous"))
        if yoy_available:
            merged = merged.merge(yoy_grouped, on=join_keys, how="left")
            yoy_column = value_column
        else:
            yoy_column = None
        merged = merged.fillna({f"{value_column}_current": 0.0, f"{value_column}_previous": 0.0})

        rows: list[dict[str, Any]] = []
        for _, row in merged.iterrows():
            current_value = float(row.get(f"{value_column}_current") or 0.0)
            previous_value = float(row.get(f"{value_column}_previous") or 0.0)
            mom_change = current_value - previous_value
            mom_change_pct = self._safe_ratio(mom_change, previous_value)
            yoy_value = row.get(yoy_column) if yoy_available and yoy_column else None
            yoy_value = float(yoy_value) if yoy_available and pd.notna(yoy_value) else None
            yoy_change = current_value - yoy_value if yoy_available and yoy_value is not None else None
            yoy_change_pct = self._safe_ratio(yoy_change, yoy_value) if yoy_available and yoy_value is not None else None
            rows.append(
                {
                    "month": current_month,
                    "previous_month": previous_month,
                    "metric": metric,
                    "dimension": dimension,
                    "name": self._dimension_row_name(row, dimension),
                    "platform": row.get(COL_PLATFORM) if dimension == "platform" else None,
                    "group_code": str(row.get(COL_GROUP_CODE)) if dimension == "business_group" and pd.notna(row.get(COL_GROUP_CODE)) else None,
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "mom_change": mom_change,
                    "mom_change_pct": mom_change_pct,
                    "mom_direction": self._change_direction(mom_change),
                    "yoy_available": yoy_available and yoy_value is not None,
                    "yoy_change": yoy_change,
                    "yoy_change_pct": yoy_change_pct,
                    "yoy_reason": yoy_reason if yoy_available and yoy_value is not None else "prior-year same month data is unavailable",
                    "severity": self._severity_from_pct(mom_change_pct),
                }
            )
        return rows

    def _aggregate_dimension_snapshot(self, df: pd.DataFrame, dimension: str, value_column: str) -> pd.DataFrame:
        if df.empty:
            if dimension == "platform":
                return pd.DataFrame(columns=[COL_PLATFORM, value_column])
            return pd.DataFrame(columns=[COL_GROUP_CODE, value_column])

        if dimension == "platform":
            return df.groupby(COL_PLATFORM, as_index=False)[value_column].sum(min_count=1)

        grouped = df.groupby(COL_GROUP_CODE, as_index=False)[value_column].sum(min_count=1)
        grouped["name"] = grouped[COL_GROUP_CODE].apply(self._group_display_name)
        return grouped

    @staticmethod
    def _dimension_join_keys(dimension: str) -> list[str]:
        if dimension == "platform":
            return [COL_PLATFORM]
        return [COL_GROUP_CODE]

    def _dimension_row_name(self, row: pd.Series | dict[str, Any], dimension: str) -> str:
        if dimension == "platform":
            return str(row.get(COL_PLATFORM))
        group_code = row.get(COL_GROUP_CODE)
        if pd.isna(group_code):
            return "unknown_group"
        return self._group_display_name(group_code)

    @staticmethod
    def _top_contributor(payload: dict[str, Any]) -> dict[str, Any] | None:
        contributors = payload.get("contributors") if payload else None
        if not contributors:
            return None
        return contributors[0]

    @staticmethod
    def _candidate_confidence(supporting_tools: list[str]) -> str:
        unique_tools = list(dict.fromkeys(supporting_tools))
        return "medium" if len(unique_tools) >= 2 else "low"

    @staticmethod
    def _candidate_direction(change: Any) -> str:
        try:
            numeric = float(change or 0.0)
        except (TypeError, ValueError):
            return "mixed"
        if numeric < 0:
            return "negative"
        if numeric > 0:
            return "positive"
        return "mixed"

    @staticmethod
    def _candidate_direction_label(direction: Any) -> str:
        if direction == "negative":
            return "負向"
        if direction == "positive":
            return "正向"
        return "混合"

    @staticmethod
    def _candidate_priority(direction: str) -> int:
        if direction == "negative":
            return 0
        if direction == "mixed":
            return 1
        return 2

    @staticmethod
    def _candidate_signal_magnitude(value: Any, invert: bool = False) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, 1.0 - numeric) if invert else abs(numeric)

    @staticmethod
    def _find_matching_turnover(
        rows: list[dict[str, Any]],
        *,
        platform: str | None = None,
        group_code: str | None = None,
    ) -> dict[str, Any] | None:
        for row in rows:
            if platform and str(row.get("platform")) != str(platform):
                continue
            if group_code is not None and str(row.get("group_code")) != str(group_code):
                continue
            return row
        return None

    @staticmethod
    def _find_matching_anomaly(
        rows: list[dict[str, Any]],
        *,
        platform: str | None = None,
        group_code: str | None = None,
    ) -> dict[str, Any] | None:
        for row in rows:
            if platform and str(row.get(COL_PLATFORM)) != str(platform):
                continue
            if group_code is not None and str(row.get(COL_GROUP_CODE)) != str(group_code):
                continue
            return row
        return None

    @staticmethod
    def _find_matching_ratio(
        rows: list[dict[str, Any]],
        *,
        platform: str | None = None,
        group_code: str | None = None,
    ) -> dict[str, Any] | None:
        for row in rows:
            if platform and str(row.get("platform")) != str(platform):
                continue
            if group_code is not None and str(row.get("group_code")) != str(group_code):
                continue
            return row
        return None

    def _group_display_name(self, group_code: Any) -> str:
        mapping = self.context.parsed_mapping.business_group_mapping
        if not mapping.empty:
            if COL_GROUP_CODE in mapping.columns and COL_GROUP_NAME in mapping.columns:
                matched = mapping.loc[mapping[COL_GROUP_CODE].astype(str) == str(group_code)]
                if not matched.empty:
                    return str(matched.iloc[0][COL_GROUP_NAME])
            if "事業群代碼" in mapping.columns and "事業群名稱" in mapping.columns:
                matched = mapping.loc[mapping["事業群代碼"].astype(str) == str(group_code)]
                if not matched.empty:
                    return str(matched.iloc[0]["事業群名稱"])
        return f"group_{group_code}"

    @staticmethod
    def _sum_metric_value(df: pd.DataFrame, value_column: str) -> float:
        if df.empty or value_column not in df.columns:
            return 0.0
        value = df[value_column].sum(min_count=1)
        if pd.isna(value):
            return 0.0
        return float(value)

    @staticmethod
    def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator in {None, 0}:
            return None
        return float(numerator) / float(denominator)

    @staticmethod
    def _change_direction(change: float | None) -> str:
        if change is None:
            return "unknown"
        if change > 0:
            return "up"
        if change < 0:
            return "down"
        return "flat"

    @staticmethod
    def _severity_from_pct(change_pct: float | None) -> str:
        if change_pct is None:
            return "low"
        magnitude = abs(change_pct)
        if magnitude >= 0.2:
            return "high"
        if magnitude >= 0.1:
            return "medium"
        return "low"

    @staticmethod
    def _shift_year_month(month: str, year_offset: int) -> str | None:
        try:
            year_text, month_text = month.split("-", 1)
            year = int(year_text) + year_offset
            month_value = int(month_text)
        except (ValueError, AttributeError):
            return None
        return f"{year:04d}-{month_value:02d}"

    @staticmethod
    def _efficiency_level(ratio: Any, *, is_comparable: bool = True) -> str:
        if not is_comparable:
            return "invalid_non_comparable"
        if ratio is None or pd.isna(ratio):
            return "unknown"
        ratio_value = float(ratio)
        if ratio_value < 0:
            return "invalid_non_comparable"
        if ratio_value >= 1.2:
            return "high"
        if ratio_value >= 0.8:
            return "medium"
        return "low"

    @staticmethod
    def _inventory_proxy_comparability(revenue: Any, inventory_amount: Any) -> tuple[bool, str | None]:
        try:
            revenue_value = None if revenue is None or pd.isna(revenue) else float(revenue)
            inventory_value = None if inventory_amount is None or pd.isna(inventory_amount) else float(inventory_amount)
        except (TypeError, ValueError):
            return False, "non_numeric_proxy_component"
        if revenue_value is None or inventory_value is None:
            return False, "missing_revenue_or_inventory_amount"
        if revenue_value <= 0:
            return False, "non_positive_revenue_numerator"
        if inventory_value <= 0:
            return False, "non_positive_inventory_denominator"
        return True, None

    @staticmethod
    def _efficiency_sort_order(level: Any) -> int:
        return {
            "low": 0,
            "medium": 1,
            "high": 2,
            "unknown": 3,
            "invalid_non_comparable": 4,
        }.get(str(level), 5)

    @staticmethod
    def _inventory_proxy_risk_label(level: str) -> str:
        return {
            "high": "healthy_proxy",
            "medium": "monitor_proxy",
            "low": "low_efficiency_proxy",
            "unknown": "insufficient_proxy_data",
            "invalid_non_comparable": "non_comparable_proxy",
        }.get(level, "insufficient_proxy_data")

    def _build_month_observation_table(self, request: ObservationRequest) -> dict[str, Any]:
        filters = QueryFilters(platform=request.platform, group_code=request.group_code)
        metric_name = {
            "revenue": "revenue_trend",
            "inventory_amount": "inventory_amount_trend",
            "inventory_qty": "inventory_qty_trend",
        }.get(request.metric, "revenue_trend")
        metric_config = self._metric_config(request.metric)
        df = self.get_metric_table(metric_name, filters).copy()
        if df.empty:
            return {
                "title": "資料觀察",
                "columns": ["月份", metric_config["label"], "前一期", "變化量", "成長率"],
                "rows": [],
                "message": "目前沒有可供比較的資料。",
            }

        value_column = metric_config["column"]
        compare_column = f"前一期{metric_config['label']}"
        change_column = f"{metric_config['label']}變化"
        growth_column = f"{metric_config['label']}成長率"

        observed = df.sort_values(COL_MONTH).reset_index(drop=True)
        observed[compare_column] = observed[value_column].shift(1)
        observed[change_column] = observed[value_column] - observed[compare_column]
        observed[growth_column] = observed["月增率"]

        rows = []
        for _, row in observed.iterrows():
            rows.append(
                {
                    "月份": row.get(COL_MONTH),
                    metric_config["label"]: self._normalize_number(row.get(value_column)),
                    "前一期": self._normalize_number(row.get(compare_column)),
                    "變化量": self._normalize_number(row.get(change_column)),
                    "成長率": row.get(growth_column),
                }
            )

        return {
            "title": f"{metric_config['label']}月份觀察",
            "columns": ["月份", metric_config["label"], "前一期", "變化量", "成長率"],
            "rows": rows,
            "message": None,
        }

    def _build_dimension_observation_table(
        self,
        request: ObservationRequest,
        current_month: str | None,
        compare_month: str | None,
    ) -> dict[str, Any]:
        metric_config = self._metric_config(request.metric)
        dimension = self._normalize_observation_dimension(request.row_dimension)
        row_label = display_label_for_dimension(dimension)
        current_df = self._build_dimension_snapshot(request, current_month)
        compare_df = self._build_dimension_snapshot(request, compare_month) if compare_month else pd.DataFrame()

        if current_df.empty:
            return {
                "title": f"{row_label}{metric_config['label']}比較",
                "columns": [row_label, "當期", "比較期", "變化量", "成長率"],
                "rows": [],
                "message": "目前條件下沒有可供比較的資料。",
            }

        join_key = row_label
        merged = current_df.merge(compare_df, on=join_key, how="left", suffixes=("_current", "_compare"))
        current_col = f"{metric_config['label']}_current"
        compare_col = f"{metric_config['label']}_compare"
        merged["變化量"] = merged[current_col] - merged[compare_col]
        merged["成長率"] = (merged["變化量"] / merged[compare_col]).replace([float("inf"), -float("inf")], pd.NA)

        rows = []
        for _, row in merged.iterrows():
            rows.append(
                {
                    row_label: row.get(join_key),
                    "當期": self._normalize_number(row.get(current_col)),
                    "比較期": self._normalize_number(row.get(compare_col)),
                    "變化量": self._normalize_number(row.get("變化量")),
                    "成長率": row.get("成長率"),
                }
            )

        title_month = current_month or "最新月份"
        compare_label = compare_month or ("前一期" if request.compare_mode == "previous_period" else "未指定")
        return {
            "title": f"{title_month}{row_label}{metric_config['label']}比較",
            "columns": [row_label, "當期", "比較期", "變化量", "成長率"],
            "rows": rows,
            "message": f"當期：{title_month}；比較期：{compare_label}",
        }

    def _build_dimension_snapshot(self, request: ObservationRequest, month: str | None) -> pd.DataFrame:
        metric_config = self._metric_config(request.metric)
        value_column = metric_config["column"]
        dimension = self._normalize_observation_dimension(request.row_dimension)
        row_label = display_label_for_dimension(dimension)
        filters = QueryFilters(month=month, platform=request.platform, group_code=request.group_code)
        df = self.get_metric_table("platform_monthly", filters).copy()
        if request.product_line_5 and "product_line_5" in df.columns:
            df = df[df["product_line_5"].astype(str) == request.product_line_5]

        if dimension == "business_group":
            label_column = COL_PLATFORM
        elif dimension == "product_line_5":
            label_column = "product_line_5"
        else:
            label_column = COL_PLATFORM

        if df.empty or label_column not in df.columns or value_column not in df.columns:
            return pd.DataFrame(columns=[row_label, metric_config["label"]])

        grouped = (
            df.groupby(label_column, as_index=False)[value_column]
            .sum(min_count=1)
            .rename(columns={label_column: row_label, value_column: metric_config["label"]})
            .sort_values(metric_config["label"], ascending=False)
            .reset_index(drop=True)
        )
        return grouped[[row_label, metric_config["label"]]]

    @staticmethod
    def _normalize_observation_dimension(row_dimension: str | None) -> str:
        if row_dimension in {"platform", "group", "business_group"}:
            return "business_group"
        if row_dimension in {"product_line", "product_line_5"}:
            return "product_line_5"
        if row_dimension == "month":
            return "month"
        return "business_group"

    def _apply_chart_type_variant(self, payload: dict[str, Any], chart_type: str) -> dict[str, Any]:
        variant = {
            **payload,
            "series": [dict(item) for item in payload.get("series", [])],
            "labels": list(payload.get("labels", [])),
        }

        if chart_type == "pie":
            return self._build_pie_payload_from_payload(variant)

        variant["chart_type"] = chart_type
        variant["title"] = self._variant_title(variant.get("title"), chart_type)
        return variant

    def _build_pie_payload_from_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        pie_rows: list[dict[str, Any]] = []
        series = payload.get("series", [])
        labels = payload.get("labels", [])

        if len(series) <= 1:
            first_series = series[0] if series else {"name": "value", "data": []}
            pie_rows = [
                {"label": label, "value": self._normalize_number(first_series.get("data", [])[index])}
                for index, label in enumerate(labels)
            ]
        else:
            for item in series:
                values = [value for value in item.get("data", []) if value is not None]
                pie_rows.append(
                    {
                        "label": item.get("name"),
                        "value": self._normalize_number(sum(values)) if values else 0,
                    }
                )

        pie_rows = [row for row in pie_rows if row.get("value") not in {None, 0}]
        return {
            **payload,
            "chart_type": "pie",
            "title": self._variant_title(payload.get("title"), "pie"),
            "labels": [row["label"] for row in pie_rows],
            "series": [{"name": "value", "data": [row["value"] for row in pie_rows]}],
            "table_preview": pie_rows,
        }

    @staticmethod
    def _variant_title(title: str | None, chart_type: str) -> str:
        base = title or "Chart"
        suffix = {
            "line": "折線圖",
            "bar": "長條圖",
            "pie": "圓餅圖",
            "area": "面積圖",
        }.get(chart_type, chart_type)
        return f"{base}（{suffix}）"

    @staticmethod
    def _build_table_preview_from_payload(payload: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
        labels = payload.get("labels", [])
        series = payload.get("series", [])
        rows: list[dict[str, Any]] = []
        for index, label in enumerate(labels[:limit]):
            row = {"label": label}
            for item in series:
                row[item.get("name", "value")] = item.get("data", [])[index] if index < len(item.get("data", [])) else None
            rows.append(row)
        return rows
