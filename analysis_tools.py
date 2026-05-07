from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


@dataclass
class QueryFilters:
    month: str | None = None
    platform: str | None = None
    group_code: str | None = None


@dataclass
class ObservationRequest:
    row_dimension: str = "platform"
    metric: str = "revenue"
    compare_mode: str = "previous_period"
    current_month: str | None = None
    compare_month: str | None = None
    platform: str | None = None
    group_code: str | None = None


class AnalysisToolbox:
    """Tool layer that wraps the existing analysis artifacts without rewriting them."""

    _CHART_DEFINITIONS = {
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
            "title": "各新事業群營收分布",
            "x_label": "新事業群",
            "y_label": "營收",
            "label_column": "事業群名稱",
            "value_column": COL_REVENUE,
            "series_name": "營收",
        },
        "inventory_by_group_bar": {
            "metric": "inventory_by_group",
            "chart_type": "bar",
            "title": "各新事業群庫存金額分布",
            "x_label": "新事業群",
            "y_label": "庫存金額",
            "label_column": "事業群名稱",
            "value_column": COL_INV_AMOUNT,
            "series_name": "庫存金額",
        },
        "platform_monthly_revenue": {
            "metric": "platform_monthly",
            "chart_type": "line",
            "title": "各平台每月營收",
            "x_label": "月份",
            "y_label": "營收",
            "label_column": COL_MONTH,
            "group_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
        },
        "platform_monthly_inventory_amount": {
            "metric": "platform_monthly",
            "chart_type": "line",
            "title": "各平台每月庫存金額",
            "x_label": "月份",
            "y_label": "庫存金額",
            "label_column": COL_MONTH,
            "group_column": COL_PLATFORM,
            "value_column": COL_INV_AMOUNT,
        },
        "platform_monthly_inventory_qty": {
            "metric": "platform_monthly",
            "chart_type": "line",
            "title": "各平台每月庫存QTY",
            "x_label": "月份",
            "y_label": "庫存QTY",
            "label_column": COL_MONTH,
            "group_column": COL_PLATFORM,
            "value_column": COL_INV_QTY,
        },
        "platform_ratio_rank": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "平台營收/庫存金額比值排行（由弱到強）",
            "x_label": "月份 / 平台 / 群組",
            "y_label": "營收/庫存金額比值",
            "label_column": "chart_label",
            "value_column": COL_REVENUE_INV_AMOUNT_RATIO,
            "series_name": "營收/庫存金額比值",
        },
        "current_month_platform_revenue_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各平台營收比較",
            "x_label": "平台",
            "y_label": "營收",
            "label_column": COL_PLATFORM,
            "value_column": COL_REVENUE,
            "series_name": "營收",
            "default_latest_month": True,
        },
        "current_month_platform_inventory_bar": {
            "metric": "platform_monthly",
            "chart_type": "bar",
            "title": "最新月份各平台庫存金額比較",
            "x_label": "平台",
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
            "x_label": "月份 / 平台 / 類型",
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
        "anomalies": {"month", "platform", "group_code"},
        "correlations": set(),
    }

    def __init__(self, context: PipelineContext, request_id: str) -> None:
        self.context = context
        self.request_id = request_id

    def get_data_coverage(self) -> dict[str, Any]:
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
    ) -> list[dict[str, Any]]:
        logger = get_logger("analysis_tools", self.request_id, domain="toolbox")
        logger.info("Running tool get_inventory_turnover_proxy top_n=%s", top_n)
        filters = filters or QueryFilters()
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
            efficiency_level = self._efficiency_level(amount_ratio)
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
                    "efficiency_level": efficiency_level,
                    "risk_label": self._inventory_proxy_risk_label(efficiency_level),
                    "limitation": "此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。",
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
        effective_filters = QueryFilters(
            month=month or filters.month,
            platform=filters.platform,
            group_code=filters.group_code,
        )
        current_month = effective_filters.month or self._latest_month_for_metric("revenue", effective_filters)
        limitations = [
            "此為 deterministic platform performance scorecard，仍未納入毛利、訂單、出貨、價格與客戶結構。",
            "營收/庫存效率為 proxy，不等於正式庫存週轉率。",
        ]
        rubric = {
            "revenue_scale_weight": 0.30,
            "revenue_momentum_weight": 0.20,
            "inventory_efficiency_weight": 0.35,
            "anomaly_score_weight": 0.15,
        }
        if current_month is None:
            limitations.append("目前沒有可用月份，無法產生平台 performance snapshot。")
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
            limitations.append("指定月份沒有平台層營收與庫存對齊資料。")
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
            limitations.append("缺少可比較的前期平台營收資料，營收動能分數未納入 health_score。")

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
                    "recommended_check": "建議進一步檢查該平台訂單、出貨、價格或客戶變化。",
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
                    "recommended_check": "建議進一步檢查該新事業群對應平台的近期訂單、出貨或客戶結構變化。",
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
                    "recommended_check": "建議進一步檢查該平台或新事業群的庫存結構、出貨節奏與近期營收變化。",
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
                    "recommended_check": "建議進一步檢查該平台或新事業群的近期營收、庫存與出貨節奏是否出現背離。",
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

        result = {
            "row_dimensions": [
                {"value": "month", "label": "月份"},
                {"value": "platform", "label": "平台"},
                {"value": "group", "label": "事業群"},
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
        if label_column == COL_PLATFORM and value_column in df.columns and COL_PLATFORM in df.columns:
            ordered = (
                df.groupby(COL_PLATFORM, as_index=False)[value_column]
                .sum(min_count=1)
                .sort_values(value_column, ascending=False)
                .head(top_n)
                .reset_index(drop=True)
            )
        else:
            ordered = df.sort_values(value_column, ascending=False).head(top_n).reset_index(drop=True)
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
        ordered = df.sort_values(COL_REVENUE_INV_AMOUNT_RATIO, ascending=True).head(top_n).copy()
        ordered["chart_label"] = ordered.apply(
            lambda row: f"{row.get(COL_MONTH)} / {row.get(COL_PLATFORM)} / G{row.get(COL_GROUP_CODE)}",
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
            lambda row: f"{row.get(COL_MONTH)} / {row.get(COL_PLATFORM) or '整體'} / {row.get(COL_ANOMALY_TYPE)}",
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
                    "name": definition.get("series_name", COL_ANOMALY_SIGNAL),
                    "data": [self._normalize_number(value) for value in ordered["signal_abs"].tolist()],
                }
            ],
            "filters": self._filters_to_dict(filters),
            "table_preview": ordered[
                [COL_MONTH, COL_GROUP_CODE, COL_PLATFORM, COL_ANOMALY_TYPE, COL_ANOMALY_SIGNAL, COL_ANOMALY_REASON]
            ].to_dict(orient="records"),
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

    @staticmethod
    def _normalize_number(value: Any) -> float | int | None:
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return value
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
    def _efficiency_level(ratio: Any) -> str:
        if ratio is None or pd.isna(ratio):
            return "unknown"
        ratio_value = float(ratio)
        if ratio_value >= 1.2:
            return "high"
        if ratio_value >= 0.8:
            return "medium"
        return "low"

    @staticmethod
    def _efficiency_sort_order(level: Any) -> int:
        return {
            "low": 0,
            "unknown": 1,
            "medium": 2,
            "high": 3,
        }.get(str(level), 4)

    @staticmethod
    def _inventory_proxy_risk_label(level: str) -> str:
        return {
            "high": "healthy_proxy",
            "medium": "monitor_proxy",
            "low": "low_efficiency_proxy",
            "unknown": "insufficient_proxy_data",
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
        row_label = "平台" if request.row_dimension == "platform" else "事業群"
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

        if request.row_dimension == "platform":
            filters = QueryFilters(month=month, platform=request.platform, group_code=request.group_code)
            df = self.get_metric_table("platform_monthly", filters).copy()
            if df.empty or COL_PLATFORM not in df.columns or value_column not in df.columns:
                return pd.DataFrame(columns=["平台", metric_config["label"]])
            grouped = (
                df.groupby(COL_PLATFORM, as_index=False)[value_column]
                .sum(min_count=1)
                .rename(columns={COL_PLATFORM: "平台", value_column: metric_config["label"]})
                .sort_values(metric_config["label"], ascending=False)
                .reset_index(drop=True)
            )
            return grouped

        filters = QueryFilters(month=month, platform=request.platform, group_code=request.group_code)
        if request.metric == "revenue":
            source_df = self._apply_filters(self.context.artifacts.revenue_enriched, filters)
        else:
            source_df = self._apply_filters(self.context.artifacts.inventory_enriched, filters)
        if source_df.empty or value_column not in source_df.columns:
            return pd.DataFrame(columns=["事業群", metric_config["label"]])

        name_column = "事業群名稱" if "事業群名稱" in source_df.columns else COL_GROUP_CODE
        grouped = (
            source_df.groupby([COL_GROUP_CODE, name_column], as_index=False)[value_column]
            .sum(min_count=1)
            .rename(columns={name_column: "事業群", value_column: metric_config["label"]})
            .sort_values(metric_config["label"], ascending=False)
            .reset_index(drop=True)
        )
        return grouped[["事業群", metric_config["label"]]]

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
