from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any

import pandas as pd

from analysis_pipeline import PipelineContext
from answer_plan import AnswerPlan, build_answer_plan
from answer_contract import build_answer_contract, build_data_quality_answer_contract, render_answer_contract
from analysis_tools import AnalysisToolbox, QueryFilters
from business_answer_templates import LLM_FIELD_BOUNDARY_PROMPT, compose_evidence_first_answer
from business_question_classifier import BusinessQuestionProfile, classify_business_question, profile_to_routing_fields
from config import (
    COL_ANOMALY_REASON,
    COL_ANOMALY_SIGNAL,
    COL_ANOMALY_TYPE,
    COL_CORR_METRICS,
    COL_CORR_VALUE,
    COL_GROUP_CODE,
    COL_INV_AMOUNT,
    COL_INV_QTY,
    COL_MONTH,
    COL_PLATFORM,
    COL_REVENUE,
)
from llm_planner import LLMPlanningResult, LLMToolPlanner, ToolPlan
from llm_rewriter import LLMAnswerRewriter, build_rewrite_request
from logging_utils import get_logger
from ollama_client import OllamaClient
from task_profile import TaskProfile, build_task_profile
from utils import format_number


@dataclass
class RoutingDecision:
    question: str
    question_type: str
    intents: list[str]
    domains: list[str]
    filters: QueryFilters
    object_dimension: str | None = None
    subtasks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    business_question_type: str | None = None
    kpi_lenses: list[str] = field(default_factory=list)
    answer_strategy: str | None = None
    planned_tools: list[str] = field(default_factory=list)
    planning_source: str | None = None
    requires_limitations: bool = False


@dataclass
class DomainResult:
    domain: str
    status: str
    task: str
    key_findings: list[str]
    evidence: list[dict[str, Any]]
    warnings: list[str]
    confidence: str
    used_tools: list[str] = field(default_factory=list)


class BaseDomainAgent:
    domain_name = "base"
    domain_description = "Generic domain agent"

    def __init__(self, toolbox: AnalysisToolbox, llm_client: OllamaClient, request_id: str) -> None:
        self.toolbox = toolbox
        self.llm_client = llm_client
        self.request_id = request_id
        self.logger = get_logger(self.__class__.__name__, request_id, domain=self.domain_name)

    def handle(self, question: str, routing: RoutingDecision) -> DomainResult:
        self.logger.info("Domain agent started task=%s", routing.question)
        if self._use_deterministic_tools(routing):
            selected_tools = self._deterministic_selected_tools(routing)
            raw_result = self.execute_tools(selected_tools, routing)
            self.logger.info("Domain agent finished deterministic status=%s tools=%s", raw_result.status, raw_result.used_tools)
            return raw_result

        selected_tools = self._plan_tools_with_llm(question, routing)
        raw_result = self.execute_tools(selected_tools, routing)
        synthesized = self._synthesize_with_llm(question, routing, raw_result)
        result = self._merge_synthesized_result(raw_result, synthesized)
        self.logger.info("Domain agent finished status=%s tools=%s", result.status, result.used_tools)
        return result

    def supported_tools(self) -> dict[str, str]:
        raise NotImplementedError

    def default_tools(self, routing: RoutingDecision) -> list[str]:
        raise NotImplementedError

    def execute_tools(self, selected_tools: list[str], routing: RoutingDecision) -> DomainResult:
        raise NotImplementedError

    @staticmethod
    def _use_deterministic_tools(routing: RoutingDecision) -> bool:
        return routing.answer_strategy in {
            "ranking",
            "trend",
            "comparison",
            "diagnosis",
            "risk",
            "performance_weakness",
            "chart",
            "decision",
            "data_quality",
            "metric_query",
        }

    def _plan_tools_with_llm(self, question: str, routing: RoutingDecision) -> list[str]:
        tool_catalog = self._available_tool_catalog()
        defaults = [tool for tool in self.default_tools(routing) if tool in tool_catalog]
        if not tool_catalog:
            self.logger.warning("No available tools registered for domain=%s", self.domain_name)
            return defaults
        system_prompt = (
            f"You are the {self.domain_name} domain planner. "
            "Choose only from the provided tools. Return JSON with a single key named tools."
        )
        user_prompt = (
            f"Question: {question}\n"
            f"Domain: {self.domain_name}\n"
            f"Question type: {routing.question_type}\n"
            f"Filters: {json.dumps(asdict(routing.filters), ensure_ascii=False)}\n"
            f"Candidate tools: {json.dumps(tool_catalog, ensure_ascii=False, indent=2)}\n"
            f"Default tools: {json.dumps(defaults, ensure_ascii=False)}\n"
            'Return example: {"tools": ["tool_name"]}'
        )
        result = self.llm_client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.0)
        if not result.ok:
            self.logger.info("LLM tool planning unavailable, using defaults")
            return defaults

        planned = result.data.get("tools", []) if result.data else []
        selected = [tool for tool in planned if tool in tool_catalog]
        if not selected:
            return defaults
        return list(dict.fromkeys(selected))

    def _available_tool_catalog(self) -> dict[str, str]:
        catalog = self.supported_tools()
        return {tool_name: description for tool_name, description in catalog.items() if self._tool_is_available(tool_name)}

    def _deterministic_selected_tools(self, routing: RoutingDecision) -> list[str]:
        tool_catalog = self._available_tool_catalog()
        planned_tools = [tool for tool in getattr(routing, "planned_tools", []) if tool in tool_catalog]
        if planned_tools:
            return list(dict.fromkeys(planned_tools))
        return [tool for tool in self.default_tools(routing) if tool in tool_catalog]

    def _tool_is_available(self, tool_name: str) -> bool:
        capability_matrix = self.toolbox.get_tool_capability_matrix()
        if tool_name.startswith("get_metric_table(") and tool_name.endswith(")"):
            metric = tool_name[len("get_metric_table("):-1]
            return capability_matrix["metrics"].get(metric, {}).get("available", True)
        if tool_name.startswith("get_top_groups(") and tool_name.endswith(")"):
            metric = tool_name[len("get_top_groups("):-1]
            if metric == "revenue":
                return not self.toolbox.context.artifacts.revenue_enriched.empty
            if metric == "inventory":
                return not self.toolbox.context.artifacts.inventory_enriched.empty
            return False
        if tool_name.startswith("get_platform_ranking(") and tool_name.endswith(")"):
            return not self.toolbox.context.artifacts.platform_monthly_analysis.empty
        if tool_name.startswith("get_yoy_mom_breakdown(") and tool_name.endswith(")"):
            metric = tool_name[len("get_yoy_mom_breakdown("):-1]
            return capability_matrix["tools"].get("get_yoy_mom_breakdown", {}).get("available", False) and (
                metric in capability_matrix["tools"].get("get_yoy_mom_breakdown", {}).get("supported_metrics", [])
            )
        if tool_name.startswith("get_contribution_analysis(") and tool_name.endswith(")"):
            metric = tool_name[len("get_contribution_analysis("):-1]
            return capability_matrix["tools"].get("get_contribution_analysis", {}).get("available", False) and (
                metric in capability_matrix["tools"].get("get_contribution_analysis", {}).get("supported_metrics", [])
            )
        if tool_name == "get_inventory_turnover_proxy":
            return capability_matrix["tools"].get("get_inventory_turnover_proxy", {}).get("available", False)
        if tool_name == "get_root_cause_candidates":
            return capability_matrix["tools"].get("get_root_cause_candidates", {}).get("available", False)
        return capability_matrix["tools"].get(tool_name, {}).get("available", True)

    def _synthesize_with_llm(
        self,
        question: str,
        routing: RoutingDecision,
        raw_result: DomainResult,
    ) -> dict[str, Any] | None:
        system_prompt = (
            f"You are the {self.domain_name} analysis agent using tool outputs only. "
            "Summarize the result faithfully and return JSON. "
            f"{LLM_FIELD_BOUNDARY_PROMPT}"
        )
        user_prompt = (
            "Return JSON with keys: key_findings, warnings, confidence.\n"
            f"Question: {question}\n"
            f"Routing: {json.dumps({'question_type': routing.question_type, 'filters': asdict(routing.filters)}, ensure_ascii=False)}\n"
            f"Current domain result: {json.dumps(asdict(raw_result), ensure_ascii=False, indent=2)}"
        )
        result = self.llm_client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.1)
        if not result.ok or not result.data:
            return None
        return result.data

    def _merge_synthesized_result(self, raw_result: DomainResult, synthesized: dict[str, Any] | None) -> DomainResult:
        if not synthesized:
            return raw_result

        key_findings = synthesized.get("key_findings")
        warnings = synthesized.get("warnings")
        confidence = synthesized.get("confidence")

        if isinstance(key_findings, list) and key_findings:
            raw_result.key_findings = [str(item) for item in key_findings]
        if isinstance(warnings, list):
            raw_result.warnings = [str(item) for item in warnings]
        if isinstance(confidence, str) and confidence in {"high", "medium", "low"}:
            raw_result.confidence = confidence
        return raw_result

    @staticmethod
    def _has_scope(filters: QueryFilters) -> bool:
        return any(value is not None for value in asdict(filters).values())

    @staticmethod
    def _is_trend_question(question: str) -> bool:
        lowered = question.lower()
        keywords = ["趨勢", "走勢", "變化", "trend", "growth", "monthly", "月增"]
        return any(keyword in question for keyword in keywords) or any(keyword in lowered for keyword in keywords)

    @staticmethod
    def _describe_trend_direction(df: pd.DataFrame, value_column: str) -> str:
        if df.empty or len(df) < 2:
            return "資料點不足，暫時無法判斷長期趨勢方向。"

        ordered = df.sort_values("月份").reset_index(drop=True)
        start_value = ordered.iloc[0][value_column]
        end_value = ordered.iloc[-1][value_column]
        if pd.isna(start_value) or pd.isna(end_value):
            return "資料中存在缺值，暫時無法穩定判斷趨勢方向。"

        if end_value > start_value:
            direction = "整體呈上升"
        elif end_value < start_value:
            direction = "整體呈下降"
        else:
            direction = "整體持平"

        return (
            f"{direction}，從 {ordered.iloc[0]['月份']} 的 {format_number(start_value)} "
            f"到 {ordered.iloc[-1]['月份']} 的 {format_number(end_value)}。"
        )

    @staticmethod
    def _recent_points_summary(df: pd.DataFrame, value_column: str, decimals: int = 2) -> str:
        if df.empty:
            return "目前沒有可用的近期資料。"

        recent = df.sort_values("月份").tail(3)
        parts: list[str] = []
        for _, row in recent.iterrows():
            mom = row.get("月增率")
            mom_text = "N/A" if pd.isna(mom) else f"{mom:.2%}"
            parts.append(
                f"{row.get('月份')}={format_number(row.get(value_column), decimals=decimals)}"
                f"（月增率 {mom_text}）"
            )
        return "最近 3 個月: " + "；".join(parts) + "。"


class SalesAgent(BaseDomainAgent):
    domain_name = "sales"
    domain_description = "Revenue and sales trend analysis"

    def supported_tools(self) -> dict[str, str]:
        return {
            "get_metric_table(revenue_trend)": "Return revenue trend table filtered by month, platform, or business group.",
            "get_top_groups(revenue)": "Return revenue ranking by business group.",
            "get_yoy_mom_breakdown(revenue)": "Return deterministic month-over-month and year-over-year revenue breakdown.",
            "get_contribution_analysis(revenue)": "Return deterministic contribution analysis for revenue change.",
            "get_root_cause_candidates": "Return deterministic candidate observations for possible drivers without claiming causal root cause.",
        }

    def default_tools(self, routing: RoutingDecision) -> list[str]:
        question_lower = routing.question.lower()
        contribution_like = any(token in routing.question for token in ["貢獻", "主要由誰", "誰帶動"]) or any(
            token in question_lower for token in ["contribution", "contributed", "who drove", "who contributed"]
        )
        tools = ["get_metric_table(revenue_trend)"]
        if routing.answer_strategy == "ranking":
            tools.append("get_top_groups(revenue)")
        if routing.answer_strategy in {"trend", "comparison", "diagnosis"}:
            tools.append("get_yoy_mom_breakdown(revenue)")
        if routing.answer_strategy in {"comparison", "diagnosis"}:
            tools.append("get_contribution_analysis(revenue)")
        if routing.answer_strategy == "diagnosis":
            tools.append("get_root_cause_candidates")
        if contribution_like:
            tools.append("get_contribution_analysis(revenue)")
        elif not self._has_scope(routing.filters):
            tools.append("get_top_groups(revenue)")
        return tools

    def execute_tools(self, selected_tools: list[str], routing: RoutingDecision) -> DomainResult:
        findings: list[str] = []
        evidence: list[dict[str, Any]] = []
        warnings: list[str] = []

        if "get_metric_table(revenue_trend)" in selected_tools:
            monthly = self.toolbox.get_metric_table("revenue_trend", routing.filters)
            if not monthly.empty:
                if routing.filters.month and len(monthly) == 1:
                    row = monthly.iloc[0]
                    findings.append(f"{row.get('月份')} 的營收為 {format_number(row.get('營收'))}。")
                else:
                    ordered = monthly.sort_values("月份").reset_index(drop=True)
                    latest = ordered.iloc[-1]
                    findings.append(
                        f"符合條件範圍內最新月份營收為 {format_number(latest.get('營收'))}"
                        f"（{latest.get('月份')}）。"
                    )
                    if self._is_trend_question(routing.question) or len(ordered) > 1:
                        findings.append(self._recent_points_summary(ordered, "營收"))
                        findings.append(self._describe_trend_direction(ordered, "營收"))
                evidence.extend(monthly.tail(3).to_dict(orient="records"))
            else:
                warnings.append("目前沒有符合條件的營收資料可供分析。")

        if "get_top_groups(revenue)" in selected_tools:
            group_rank = self.toolbox.get_top_groups("revenue", filters=routing.filters)
            if group_rank:
                top_group = group_rank[0]
                findings.append(
                    f"整體營收最高的新事業群是 {top_group['group_name']}（代碼 {top_group['group_code']}），"
                    f"累計營收 {top_group['value_text']}。"
                )
                evidence.extend(group_rank[:3])

        if "get_yoy_mom_breakdown(revenue)" in selected_tools:
            yoy_dimension = "overall"
            if routing.object_dimension == "platform":
                yoy_dimension = "platform"
            elif routing.object_dimension == "business_group":
                yoy_dimension = "business_group"
            yoy_rows = self.toolbox.get_yoy_mom_breakdown(
                routing.filters,
                metric="revenue",
                dimension=yoy_dimension,
                top_n=3,
            )
            if yoy_rows:
                first = yoy_rows[0]
                findings.append(
                    f"{first['month']} 營收相較 {first['previous_month']} "
                    f"{'增加' if first['mom_change'] > 0 else ('下降' if first['mom_change'] < 0 else '持平')} "
                    f"{format_number(abs(first['mom_change']))}。"
                )
                if first.get("mom_change_pct") is not None:
                    findings.append(f"MoM 變化率為 {first['mom_change_pct']:.2%}。")
                if not first.get("yoy_available"):
                    findings.append("目前沒有去年同期資料，因此暫時無法提供 YoY。")
                evidence.extend(yoy_rows)

        if "get_contribution_analysis(revenue)" in selected_tools:
            contribution_dimension = "platform" if routing.object_dimension == "platform" else "business_group"
            contribution = self.toolbox.get_contribution_analysis(
                routing.filters,
                metric="revenue",
                dimension=contribution_dimension,
                top_n=3,
            )
            if contribution.get("contributors"):
                first = contribution["contributors"][0]
                findings.append(
                    f"{contribution['month']} 相較 {contribution['previous_month']} 的營收變化，"
                    f"主要由 {first['name']} 貢獻，變動 {format_number(first['change'])}。"
                )
                evidence.append(contribution)

        if "get_root_cause_candidates" in selected_tools:
            candidates = self.toolbox.get_root_cause_candidates(routing.filters, metric="revenue", top_n=4)
            if candidates.get("candidates"):
                first = candidates["candidates"][0]
                findings.append(f"已整理出候選觀察方向；優先可先檢查 {first['title']}。")
                evidence.append(candidates)

        status = "success" if findings else "partial"
        confidence = "high" if findings else "low"
        return DomainResult(
            domain="sales",
            status=status,
            task="營收 / 銷售趨勢分析",
            key_findings=findings or ["目前無法產出有效的營收分析。"],
            evidence=evidence,
            warnings=warnings,
            confidence=confidence,
            used_tools=selected_tools,
        )


class InventoryAgent(BaseDomainAgent):
    domain_name = "inventory"
    domain_description = "Inventory amount and quantity analysis"

    def supported_tools(self) -> dict[str, str]:
        return {
            "get_metric_table(inventory_amount_trend)": "Return inventory amount trend filtered by scope.",
            "get_metric_table(inventory_qty_trend)": "Return inventory quantity trend filtered by scope.",
            "get_top_groups(inventory)": "Return inventory ranking by business group.",
            "get_platform_ranking(inventory_amount)": "Return inventory amount ranking by platform.",
            "get_yoy_mom_breakdown(inventory_amount)": "Return deterministic month-over-month and year-over-year inventory amount breakdown.",
            "get_yoy_mom_breakdown(inventory_qty)": "Return deterministic month-over-month and year-over-year inventory quantity breakdown.",
            "get_contribution_analysis(inventory_amount)": "Return deterministic contribution analysis for inventory amount change.",
            "get_inventory_turnover_proxy": "Return revenue to inventory proxy efficiency records.",
        }

    def default_tools(self, routing: RoutingDecision) -> list[str]:
        question_lower = routing.question.lower()
        efficiency_like = any(token in routing.question for token in ["效率", "週轉", "周轉", "比值"]) or any(
            token in question_lower for token in ["efficiency", "turnover", "ratio"]
        )
        tools = [
            "get_metric_table(inventory_amount_trend)",
            "get_metric_table(inventory_qty_trend)",
        ]
        if (
            routing.object_dimension == "platform"
            and not routing.filters.platform
            and routing.answer_strategy != "performance_weakness"
        ):
            tools.append("get_platform_ranking(inventory_amount)")
        elif not self._has_scope(routing.filters):
            tools.append("get_top_groups(inventory)")
        if routing.answer_strategy in {"trend", "comparison", "diagnosis", "risk", "performance_weakness"}:
            tools.append("get_yoy_mom_breakdown(inventory_amount)")
        if routing.answer_strategy in {"comparison", "diagnosis"}:
            tools.append("get_contribution_analysis(inventory_amount)")
        if routing.answer_strategy in {"diagnosis", "risk", "performance_weakness"}:
            tools.append("get_inventory_turnover_proxy")
        if efficiency_like:
            tools.append("get_inventory_turnover_proxy")
        return tools

    def execute_tools(self, selected_tools: list[str], routing: RoutingDecision) -> DomainResult:
        findings: list[str] = []
        evidence: list[dict[str, Any]] = []
        warnings: list[str] = []

        if "get_metric_table(inventory_amount_trend)" in selected_tools:
            amount = self.toolbox.get_metric_table("inventory_amount_trend", routing.filters)
            if not amount.empty:
                if routing.filters.month and len(amount) == 1:
                    row = amount.iloc[0]
                    findings.append(f"{row.get('月份')} 的庫存金額為 {format_number(row.get('金額'))}。")
                else:
                    ordered = amount.sort_values("月份").reset_index(drop=True)
                    latest = ordered.iloc[-1]
                    findings.append(
                        f"符合條件範圍內最新月份庫存金額為 {format_number(latest.get('金額'))}"
                        f"（{latest.get('月份')}）。"
                    )
                    if self._is_trend_question(routing.question) or len(ordered) > 1:
                        findings.append(self._recent_points_summary(ordered, "金額"))
                        findings.append(self._describe_trend_direction(ordered, "金額"))
                evidence.extend(amount.tail(3).to_dict(orient="records"))
            else:
                warnings.append("目前沒有符合條件的庫存金額資料。")

        if "get_metric_table(inventory_qty_trend)" in selected_tools:
            qty = self.toolbox.get_metric_table("inventory_qty_trend", routing.filters)
            if not qty.empty:
                if routing.filters.month and len(qty) == 1:
                    row = qty.iloc[0]
                    findings.append(f"{row.get('月份')} 的庫存 QTY 為 {format_number(row.get('QTY'), decimals=0)}。")
                else:
                    ordered = qty.sort_values("月份").reset_index(drop=True)
                    latest = ordered.iloc[-1]
                    findings.append(
                        f"符合條件範圍內最新月份庫存 QTY 為 {format_number(latest.get('QTY'), decimals=0)}"
                        f"（{latest.get('月份')}）。"
                    )
                    if self._is_trend_question(routing.question) or len(ordered) > 1:
                        findings.append(self._recent_points_summary(ordered, "QTY", decimals=0))
                        findings.append(self._describe_trend_direction(ordered, "QTY"))
                evidence.extend(qty.tail(3).to_dict(orient="records"))
            else:
                warnings.append("目前沒有符合條件的庫存 QTY 資料。")

        if "get_top_groups(inventory)" in selected_tools:
            group_rank = self.toolbox.get_top_groups("inventory", filters=routing.filters)
            if group_rank:
                top_group = group_rank[0]
                findings.append(
                    f"整體庫存金額最高的新事業群是 {top_group['group_name']}（代碼 {top_group['group_code']}），"
                    f"累計庫存金額 {top_group['value_text']}。"
                )
                evidence.extend(group_rank[:3])

        if "get_platform_ranking(inventory_amount)" in selected_tools:
            platform_rank = self.toolbox.get_platform_ranking("inventory_amount", filters=routing.filters)
            if platform_rank:
                top_platform = platform_rank[0]
                scope_label = f"{routing.filters.month} " if routing.filters.month else "目前累計 "
                findings.append(
                    f"{scope_label}庫存金額最高的平台是 {top_platform['platform']}，"
                    f"數值為 {top_platform['value_text']}。"
                )
                evidence.extend(platform_rank[:3])

        if "get_yoy_mom_breakdown(inventory_amount)" in selected_tools:
            yoy_dimension = "overall"
            if routing.object_dimension == "platform":
                yoy_dimension = "platform"
            elif routing.object_dimension == "business_group":
                yoy_dimension = "business_group"
            yoy_rows = self.toolbox.get_yoy_mom_breakdown(
                routing.filters,
                metric="inventory_amount",
                dimension=yoy_dimension,
                top_n=3,
            )
            if yoy_rows:
                first = yoy_rows[0]
                findings.append(
                    f"{first['month']} 庫存金額相較 {first['previous_month']} "
                    f"{'增加' if first['mom_change'] > 0 else ('下降' if first['mom_change'] < 0 else '持平')} "
                    f"{format_number(abs(first['mom_change']))}。"
                )
                evidence.extend(yoy_rows)

        if "get_contribution_analysis(inventory_amount)" in selected_tools:
            contribution_dimension = "platform" if routing.object_dimension == "platform" else "business_group"
            contribution = self.toolbox.get_contribution_analysis(
                routing.filters,
                metric="inventory_amount",
                dimension=contribution_dimension,
                top_n=3,
            )
            if contribution.get("contributors"):
                first = contribution["contributors"][0]
                findings.append(
                    f"{contribution['month']} 相較 {contribution['previous_month']} 的庫存金額變化，"
                    f"主要由 {first['name']} 貢獻，變動 {format_number(first['change'])}。"
                )
                evidence.append(contribution)

        if "get_inventory_turnover_proxy" in selected_tools:
            proxy_rows = self.toolbox.get_inventory_turnover_proxy(routing.filters, top_n=3)
            if proxy_rows:
                weakest = proxy_rows[0]
                findings.append(
                    f"庫存效率 proxy 最弱的是 {weakest['month']} / 平台 {weakest['platform']} / 新事業群 {weakest['group_code']}，"
                    f"營收/庫存金額 ratio 為 {format_number(weakest['revenue_inventory_amount_ratio'])}。"
                )
                evidence.extend(proxy_rows)

        status = "success" if findings else "partial"
        confidence = "high" if findings else "low"
        return DomainResult(
            domain="inventory",
            status=status,
            task="庫存金額 / QTY 趨勢分析",
            key_findings=findings or ["目前無法產出有效的庫存分析。"],
            evidence=evidence,
            warnings=warnings,
            confidence=confidence,
            used_tools=selected_tools,
        )


class FinancialMetricsAgent(BaseDomainAgent):
    domain_name = "financial"
    domain_description = "Financial proxy metrics and anomaly interpretation"

    def supported_tools(self) -> dict[str, str]:
        return {
            "get_platform_performance_snapshot": "Return deterministic platform performance scorecard across revenue scale, momentum, inventory-efficiency proxy, and anomalies.",
            "get_platform_ratios": "Return revenue to inventory proxy ratios on platform-month level.",
            "get_anomalies": "Return anomaly records produced by the existing analyzer.",
            "get_contribution_analysis(revenue)": "Return deterministic contribution analysis for revenue change.",
            "get_inventory_turnover_proxy": "Return revenue to inventory proxy efficiency records.",
            "get_root_cause_candidates": "Return deterministic candidate observations for possible drivers without claiming causal root cause.",
        }

    def default_tools(self, routing: RoutingDecision) -> list[str]:
        tools = ["get_platform_ratios", "get_anomalies"]
        if routing.answer_strategy in {"comparison", "performance_weakness"}:
            tools.insert(0, "get_platform_performance_snapshot")
        if routing.answer_strategy in {"comparison", "diagnosis"}:
            tools.append("get_contribution_analysis(revenue)")
        if routing.answer_strategy in {"risk", "diagnosis", "comparison", "performance_weakness"}:
            tools.append("get_inventory_turnover_proxy")
        if routing.answer_strategy in {"diagnosis", "performance_weakness"}:
            tools.append("get_root_cause_candidates")
        return tools

    def execute_tools(self, selected_tools: list[str], routing: RoutingDecision) -> DomainResult:
        findings: list[str] = []
        warnings: list[str] = []
        evidence: list[dict[str, Any]] = []
        unsupported_reasons: list[str] = []
        capability_matrix = self.toolbox.get_tool_capability_matrix()
        ratio_available = capability_matrix["tools"]["get_platform_ratios"]["available"]
        question_lower = routing.question.lower()
        ratio_question = any(token in routing.question for token in ["比值", "庫存/營收", "營收/庫存", "偏弱", "最弱", "最低"]) or any(
            token in question_lower for token in ["ratio", "weakest", "lowest"]
        )
        anomaly_question = any(token in routing.question for token in ["異常", "風險", "背離", "積壓"]) or any(
            token in question_lower for token in ["anomaly", "risk", "divergence"]
        )
        effective_tools = list(dict.fromkeys(selected_tools))

        # Keep the answer deterministic for direct financial questions even if the LLM planner
        # forgets to include the critical tool.
        if ratio_question and ratio_available and "get_platform_ratios" not in effective_tools:
            effective_tools.append("get_platform_ratios")
        if anomaly_question and "get_anomalies" not in effective_tools:
            effective_tools.append("get_anomalies")

        if ratio_question and not ratio_available:
            unsupported_reasons.append("目前資料無法形成平台層整合分析，因此無法提供穩定的營收/庫存比值工具結果。")

        if "get_platform_performance_snapshot" in effective_tools:
            snapshot = self.toolbox.get_platform_performance_snapshot(routing.filters)
            if snapshot.get("rows"):
                summary = snapshot.get("summary", {})
                findings.append(
                    "平台 performance scorecard 顯示，目前綜合表現較佳的平台為 "
                    f"{summary.get('best_platform', 'N/A')}，需優先注意的平台為 {summary.get('weakest_platform', 'N/A')}。"
                )
                evidence.append(snapshot)
            else:
                warnings.extend(snapshot.get("limitations", ["目前沒有平台 performance scorecard 結果。"]))

        if "get_platform_ratios" in effective_tools:
            if ratio_available:
                ratio_records = self.toolbox.get_platform_ratios(routing.filters)
                if ratio_records:
                    weakest = ratio_records[0]
                    findings.append(
                        "在目前可對齊的平台資料中，營收相對庫存表現最弱的組合為 "
                        f"{weakest.get('month')} / 平台 {weakest.get('platform')} / 新事業群 {weakest.get('group_code')}。"
                    )
                    findings.append(
                        f"營收/庫存金額比值 {format_number(weakest.get('revenue_inventory_amount_ratio'))}，"
                        f"營收/庫存QTY比值 {format_number(weakest.get('revenue_inventory_qty_ratio'))}。"
                    )
                    if len(ratio_records) > 1:
                        second = ratio_records[1]
                        findings.append(
                            "次弱組合為 "
                            f"{second.get('month')} / 平台 {second.get('platform')} / 新事業群 {second.get('group_code')}，"
                            f"營收/庫存金額比值 {format_number(second.get('revenue_inventory_amount_ratio'))}。"
                        )
                    evidence.extend(ratio_records[:3])
                else:
                    warnings.append("目前沒有符合條件的平台比值結果。")

        if "get_anomalies" in effective_tools:
            anomaly_records = self.toolbox.get_anomalies(filters=routing.filters)
            if anomaly_records:
                first = anomaly_records[0]
                findings.append(
                    f"目前偵測到 {len(anomaly_records)} 筆異常訊號；最需要注意的是 "
                    f"{first.get(COL_MONTH, 'N/A')} / 平台 {first.get(COL_PLATFORM, 'N/A')} / 新事業群 {first.get(COL_GROUP_CODE, 'N/A')}。"
                )
                findings.append(
                    f"異常類型為 {first.get(COL_ANOMALY_TYPE, '欄位不足')}，"
                    f"原因為 {first.get(COL_ANOMALY_REASON, '欄位不足')}，"
                    f"訊號值為 {format_number(first.get(COL_ANOMALY_SIGNAL))}。"
                )
                evidence.extend(anomaly_records[:3])
            else:
                warnings.append("目前沒有符合條件的異常偵測結果。")

        if "get_contribution_analysis(revenue)" in effective_tools:
            contribution_dimension = "platform" if routing.object_dimension == "platform" else "business_group"
            contribution = self.toolbox.get_contribution_analysis(
                routing.filters,
                metric="revenue",
                dimension=contribution_dimension,
                top_n=3,
            )
            if contribution.get("contributors"):
                first = contribution["contributors"][0]
                findings.append(
                    f"{contribution['month']} 相較 {contribution['previous_month']} 的營收變化，"
                    f"主要由 {first['name']} 貢獻，變動 {format_number(first['change'])}。"
                )
                evidence.append(contribution)

        if "get_inventory_turnover_proxy" in effective_tools:
            proxy_rows = self.toolbox.get_inventory_turnover_proxy(routing.filters, top_n=3)
            if proxy_rows:
                weakest = proxy_rows[0]
                findings.append(
                    f"庫存效率 proxy 偏弱的是 {weakest['month']} / 平台 {weakest['platform']} / 新事業群 {weakest['group_code']}，"
                    f"營收/庫存金額 ratio 為 {format_number(weakest['revenue_inventory_amount_ratio'])}。"
                )
                evidence.extend(proxy_rows[:2])

        if "get_root_cause_candidates" in effective_tools:
            candidates = self.toolbox.get_root_cause_candidates(routing.filters, metric="revenue", top_n=4)
            if candidates.get("candidates"):
                first = candidates["candidates"][0]
                findings.append(f"可先整理的候選觀察方向包括 {first['title']}。")
                evidence.append(candidates)

        if any(token in routing.question for token in ["毛利", "費用", "現金流", "EPS", "損益"]):
            warnings.append("目前資料沒有成本、費用或財報欄位，因此只能提供代理型財務分析，無法直接回答完整財務報表問題。")

        warnings.extend(unsupported_reasons)
        if findings:
            status = "success"
            confidence = "medium"
        elif unsupported_reasons:
            status = "unsupported"
            confidence = "low"
        else:
            status = "partial"
            confidence = "low"
        return DomainResult(
            domain="financial",
            status=status,
            task="財務代理指標 / 比值 / 異常分析",
            key_findings=findings or ["目前只能提供有限的財務代理指標分析。"],
            evidence=evidence,
            warnings=warnings,
            confidence=confidence,
            used_tools=effective_tools,
        )


class ChartAgent(BaseDomainAgent):
    domain_name = "chart"
    domain_description = "Chart planning, payload generation, and chart rendering"

    def supported_tools(self) -> dict[str, str]:
        return {
            "get_chart_catalog": "Return the list of available charts and supported filters.",
            "get_chart_payload": "Return a chart-ready payload for frontend rendering.",
            "get_chart_table": "Return table rows aligned with the selected chart.",
            "create_chart_image": "Render a PNG chart into output/charts and return the file path.",
        }

    def default_tools(self, routing: RoutingDecision) -> list[str]:
        return ["get_chart_payload", "get_chart_table", "create_chart_image"]

    def execute_tools(self, selected_tools: list[str], routing: RoutingDecision) -> DomainResult:
        findings: list[str] = []
        warnings: list[str] = []
        evidence: list[dict[str, Any]] = []
        effective_tools = list(dict.fromkeys(selected_tools))
        request = self._interpret_chart_request(routing.question)
        chart_key = request["chart_key"]
        chart_type_override = request["chart_type"]

        if "get_chart_payload" not in effective_tools:
            effective_tools.append("get_chart_payload")
        if "get_chart_table" not in effective_tools:
            effective_tools.append("get_chart_table")

        chart_payload = self.toolbox.get_chart_payload(
            chart_key,
            routing.filters,
            chart_type_override=chart_type_override,
            include_table=True,
        )
        if chart_payload:
            findings.append(f"已整理圖表：{chart_payload.get('title', chart_key)}")
            findings.append(
                f"圖型為 {chart_payload.get('chart_type')}，包含 {len(chart_payload.get('series', []))} 組資料序列。"
            )
            if chart_payload.get("table_preview"):
                findings.append(f"已同步提供 {len(chart_payload.get('table_preview', []))} 列表格資料。")
            evidence.append(chart_payload)
        else:
            warnings.append("目前無法依指定條件產出圖表資料。")

        if chart_payload and "get_chart_table" in effective_tools:
            table_rows = self.toolbox.get_chart_table(
                chart_key,
                routing.filters,
                chart_type_override=chart_type_override,
            )
            if table_rows:
                evidence.append(
                    {
                        "chart_key": chart_key,
                        "chart_type": chart_payload.get("chart_type"),
                        "table_preview": table_rows,
                    }
                )

        if chart_payload and "create_chart_image" in effective_tools:
            image_result = self.toolbox.create_chart_image(
                chart_key,
                routing.filters,
                chart_type_override=chart_type_override,
            )
            if image_result:
                findings.append(f"已輸出圖檔：{image_result['output_path']}")
                evidence.append(image_result)

        if "get_chart_catalog" in effective_tools:
            evidence.append({"available_charts": self.toolbox.get_chart_catalog()})

        status = "success" if chart_payload else "partial"
        confidence = "high" if chart_payload else "low"
        return DomainResult(
            domain="chart",
            status=status,
            task="圖表規劃、動態繪圖與表格整理",
            key_findings=findings or ["目前沒有可用的圖表資料。"],
            evidence=evidence,
            warnings=warnings,
            confidence=confidence,
            used_tools=effective_tools,
        )

    @staticmethod
    def _chart_key_has_any(text: str, tokens: list[str]) -> bool:
        return any(token in text for token in tokens)

    @classmethod
    def _select_chart_key(cls, question: str) -> str:
        lowered = question.lower()
        has_platform = cls._chart_key_has_any(question, ["平台", "平臺", "GG-"]) or "platform" in lowered
        has_group = cls._chart_key_has_any(question, ["事業群", "群組"]) or "group" in lowered
        asks_current_month = cls._chart_key_has_any(question, ["本月", "最新月份", "最新月", "當月"]) or any(
            token in lowered for token in ["current month", "latest month"]
        )

        if cls._chart_key_has_any(question, ["異常", "風險", "警訊"]) or any(
            token in lowered for token in ["anomaly", "risk", "warning"]
        ):
            return "anomaly_signal_rank"
        if cls._chart_key_has_any(question, ["比值", "最低", "最弱", "較差", "最差", "表現差", "偏弱", "效率"]) or any(
            token in lowered for token in ["ratio", "weakest", "lowest"]
        ):
            return "platform_ratio_rank"

        if has_platform and asks_current_month:
            if cls._chart_key_has_any(question, ["營收", "銷售"]) or any(
                token in lowered for token in ["revenue", "sales"]
            ):
                return "current_month_platform_revenue_bar"
            if "qty" in lowered or "QTY" in question:
                return "platform_monthly_inventory_qty"
            if cls._chart_key_has_any(question, ["庫存", "存貨", "金額"]) or "inventory" in lowered:
                return "current_month_platform_inventory_bar"

        if has_platform and (cls._chart_key_has_any(question, ["營收", "銷售"]) or any(
            token in lowered for token in ["revenue", "sales"]
        )):
            return "platform_monthly_revenue"
        if has_platform and ("qty" in lowered or "QTY" in question):
            return "platform_monthly_inventory_qty"
        if has_platform and (cls._chart_key_has_any(question, ["庫存", "存貨", "金額"]) or "inventory" in lowered):
            return "platform_monthly_inventory_amount"
        if has_group and (cls._chart_key_has_any(question, ["營收", "銷售", "排名", "排行"]) or any(
            token in lowered for token in ["revenue", "sales", "ranking", "rank"]
        )):
            return "revenue_by_group_bar"
        if has_group and (cls._chart_key_has_any(question, ["庫存", "存貨", "排名", "排行"]) or any(
            token in lowered for token in ["inventory", "stock", "ranking", "rank"]
        )):
            return "inventory_by_group_bar"
        if "qty" in lowered or "QTY" in question:
            return "monthly_inventory_qty_trend"
        if cls._chart_key_has_any(question, ["庫存", "存貨", "金額"]) or "inventory" in lowered:
            return "monthly_inventory_amount_trend"
        return "monthly_revenue_trend"

    @staticmethod
    def _requested_chart_type(question: str) -> str | None:
        lowered = question.lower()
        if any(token in question for token in ["圓餅圖", "餅圖"]) or "pie" in lowered:
            return "pie"
        if any(token in question for token in ["面積圖", "區域圖"]) or "area" in lowered:
            return "area"
        if any(token in question for token in ["長條圖", "柱狀圖", "條圖"]) or "bar" in lowered:
            return "bar"
        if any(token in question for token in ["折線圖", "線圖"]) or "line" in lowered:
            return "line"
        return None

    @classmethod
    def _interpret_chart_request(cls, question: str) -> dict[str, Any]:
        return {
            "chart_key": cls._select_chart_key(question),
            "chart_type": cls._requested_chart_type(question),
            "wants_table": any(token in question for token in ["表格", "資料表"]) or "table" in question.lower(),
        }


class AssociationAgent(BaseDomainAgent):
    domain_name = "association"
    domain_description = "Association and correlation fallback analysis"

    def supported_tools(self) -> dict[str, str]:
        return {
            "get_correlations": "Return the precomputed correlation analysis table.",
        }

    def default_tools(self, routing: RoutingDecision) -> list[str]:
        return ["get_correlations"]

    def execute_tools(self, selected_tools: list[str], routing: RoutingDecision) -> DomainResult:
        findings: list[str] = []
        warnings: list[str] = []
        evidence: list[dict[str, Any]] = []

        if "get_correlations" in selected_tools:
            correlations = self.toolbox.get_correlations()
            if correlations:
                top = correlations[0]
                findings.append(
                    f"目前可用的關聯分析以相關係數為主；最顯著的關係是 "
                    f"{top.get(COL_CORR_METRICS, 'N/A')}，相關係數 {format_number(top.get(COL_CORR_VALUE))}。"
                )
                evidence.extend(correlations[:3])
            else:
                warnings.append("目前沒有可用的相關分析結果。")

        lowered = routing.question.lower()
        if any(token in lowered for token in ["association rule", "market basket", "basket", "co-occurrence"]):
            warnings.append("目前資料沒有 transaction-level 明細，因此無法直接做 association rules；已改用 correlation 作為 fallback。")

        status = "success" if findings else "partial"
        confidence = "medium" if findings else "low"
        return DomainResult(
            domain="association",
            status=status,
            task="關聯 / 相關分析",
            key_findings=findings or ["目前沒有足夠資料做 association rules，僅能提供 correlation fallback。"],
            evidence=evidence,
            warnings=warnings,
            confidence=confidence,
            used_tools=selected_tools,
        )
class MultiAgentAssistant:
    # -------------------------------------------------------------------------
    # Orchestrator Setup
    # -------------------------------------------------------------------------
    def __init__(
        self,
        context: PipelineContext,
        request_id: str,
        use_llm_planner: bool | None = None,
        use_llm_rewriter: bool | None = None,
    ) -> None:
        self.context = context
        self.request_id = request_id
        self.logger = get_logger("multi_agent", request_id, domain="orchestrator")
        self.toolbox = AnalysisToolbox(context, request_id)
        self.capability_matrix = self.toolbox.get_tool_capability_matrix()
        self.llm_client = OllamaClient(request_id=request_id)
        self.use_llm_planner = (
            use_llm_planner
            if use_llm_planner is not None
            else os.getenv("USE_LLM_PLANNER", "false").strip().lower() == "true"
        )
        self.use_llm_rewriter = (
            use_llm_rewriter
            if use_llm_rewriter is not None
            else os.getenv("USE_LLM_REWRITER", "false").strip().lower() == "true"
        )
        self.llm_planner = LLMToolPlanner(request_id)
        self.llm_rewriter = LLMAnswerRewriter(request_id)
        self.agents = {
            "sales": SalesAgent(self.toolbox, self.llm_client, request_id),
            "inventory": InventoryAgent(self.toolbox, self.llm_client, request_id),
            "financial": FinancialMetricsAgent(self.toolbox, self.llm_client, request_id),
            "association": AssociationAgent(self.toolbox, self.llm_client, request_id),
            "chart": ChartAgent(self.toolbox, self.llm_client, request_id),
        }

    # -------------------------------------------------------------------------
    # Project Summary / Overview Support
    # -------------------------------------------------------------------------
    def summarize_project(self) -> dict[str, Any]:
        coverage = self.toolbox.get_data_coverage()
        mapping_summary = self.toolbox.get_mapping_summary()
        recent_snapshot = self._build_recent_snapshot(coverage["months"])
        dashboard_snapshot = self._build_dashboard_snapshot_v2(recent_snapshot)
        return {
            "project_overview": {
                "source_files": coverage["source_files"],
                "supported_domains": coverage["supported_domains"],
                "months": coverage["months"],
                "inventory_rows": coverage["inventory_rows"],
                "revenue_rows": coverage["revenue_rows"],
                "mapping_rows": coverage["mapping_rows"],
            },
            "recent_snapshot": recent_snapshot,
            "dashboard_snapshot": dashboard_snapshot,
            "latest_month_analysis": self._build_latest_month_analysis_v2(recent_snapshot, dashboard_snapshot),
            "raw_data_overview": {
                "source_files": coverage["source_files"],
                "mapping_success": coverage["mapping_success"],
                "column_counts": {
                    "inventory": len(self.context.inventory_df.columns),
                    "revenue": len(self.context.revenue_df.columns),
                    "mapping": len(self.context.parsed_mapping.structured_mapping.columns),
                },
                "row_counts": {
                    "inventory": coverage["inventory_rows"],
                    "revenue": coverage["revenue_rows"],
                    "mapping": coverage["mapping_rows"],
                },
            },
            "actual_columns": {
                "inventory": self.context.inventory_df.columns.tolist(),
                "revenue": self.context.revenue_df.columns.tolist(),
                "mapping": self.context.parsed_mapping.structured_mapping.columns.tolist(),
            },
            "mapping_summary": mapping_summary,
            "tool_capability_matrix": self.capability_matrix,
            "existing_capabilities": [
                "Excel data loading and column validation",
                "Date / numeric normalization",
                "Mapping parsing for 事業群 / HQBU / 平台",
                "Monthly trend aggregation",
                "Group ranking aggregation",
                "Partial revenue-inventory proxy ratio analysis when platform alignment is available",
                "Anomaly detection",
                "Correlation analysis",
                "Chart payload generation for frontend rendering",
                "PNG chart export for demo and reporting",
                "Markdown report / chart generation",
                "Rule-based QA retrieval",
            ],
            "recommended_agents": ["sales", "inventory", "financial", "association", "chart"],
            "not_directly_supported": [
                "transaction-level market basket association rules",
                "full financial statements such as margin / expense / cashflow",
            ],
            "minimal_change_plan": [
                "Reuse current data loader, mapping parser, and analyzer as the tool layer",
                "Let the main agent handle planning, routing, decomposition, and synthesis",
                "Let domain agents call existing tools first and use Ollama only for planning and explanation",
                "Keep current output/report pipeline unchanged for compatibility",
            ],
            "pipeline_messages": {
                "infos": self.context.messages.infos,
                "warnings": self.context.messages.warnings,
                "errors": self.context.messages.errors,
            },
        }

    def _build_recent_snapshot(self, months: list[str]) -> dict[str, Any]:
        revenue_monthly = self.toolbox.get_metric_table("revenue_monthly")
        inventory_amount_monthly = self.toolbox.get_metric_table("inventory_amount_monthly")
        inventory_qty_monthly = self.toolbox.get_metric_table("inventory_qty_monthly")

        latest_month = months[-1] if months else None
        recent_three_months = months[-3:] if months else []

        return {
            "latest_month": latest_month,
            "recent_three_months": recent_three_months,
            "current_month": {
                "month": latest_month,
                "revenue": self._lookup_metric_value(revenue_monthly, latest_month, "營收"),
                "inventory_amount": self._lookup_metric_value(inventory_amount_monthly, latest_month, "金額"),
                "inventory_qty": self._lookup_metric_value(inventory_qty_monthly, latest_month, "QTY", decimals=0),
                "revenue_mom": self._lookup_metric_value(revenue_monthly, latest_month, "月增率", decimals=4),
                "inventory_amount_mom": self._lookup_metric_value(
                    inventory_amount_monthly,
                    latest_month,
                    "月增率",
                    decimals=4,
                ),
                "inventory_qty_mom": self._lookup_metric_value(inventory_qty_monthly, latest_month, "月增率", decimals=4),
            },
            "recent_period": {
                "months": recent_three_months,
                "revenue_total": self._sum_metric_values(revenue_monthly, recent_three_months, "營收"),
                "inventory_amount_total": self._sum_metric_values(inventory_amount_monthly, recent_three_months, "金額"),
                "inventory_qty_total": self._sum_metric_values(inventory_qty_monthly, recent_three_months, "QTY", decimals=0),
            },
        }

    # Legacy overview snapshot helpers retained for compatibility with older
    # internal summary flows and ad hoc debugging. The stable answer path uses
    # the v2 variants below.
    def _build_dashboard_snapshot(self, recent_snapshot: dict[str, Any]) -> dict[str, Any]:
        latest_month = recent_snapshot.get("latest_month")
        if not latest_month:
            return {
                "latest_month": None,
                "revenue_extremes": {},
                "inventory_extremes": {},
                "anomalies": [],
            }

        platform_month = self.toolbox.get_metric_table("platform_monthly", QueryFilters(month=latest_month))
        anomalies = self.toolbox.get_anomalies(top_n=10, filters=QueryFilters(month=latest_month))

        revenue_extremes = self._build_platform_extremes(platform_month, "營收")
        inventory_extremes = self._build_platform_extremes(platform_month, "金額")
        anomaly_preview = sorted(
            anomalies,
            key=lambda item: abs(float(item.get("訊號", 0) or 0)),
            reverse=True,
        )[:3]

        return {
            "latest_month": latest_month,
            "revenue_extremes": revenue_extremes,
            "inventory_extremes": inventory_extremes,
            "anomalies": anomaly_preview,
            "anomaly_count": len(anomalies),
        }

    @staticmethod
    def _build_platform_extremes(df: pd.DataFrame, value_column: str) -> dict[str, Any]:
        if df.empty or value_column not in df.columns:
            return {}

        grouped = (
            df.groupby("平台", as_index=False)[value_column]
            .sum(min_count=1)
            .sort_values(value_column, ascending=False)
            .reset_index(drop=True)
        )
        if grouped.empty:
            return {}

        max_row = grouped.iloc[0]
        min_row = grouped.iloc[-1]
        return {
            "max_platform": max_row.get("平台"),
            "max_value": self._coerce_number(max_row.get(value_column)),
            "min_platform": min_row.get("平台"),
            "min_value": self._coerce_number(min_row.get(value_column)),
        }

    @staticmethod
    def _build_latest_month_analysis(recent_snapshot: dict[str, Any], dashboard_snapshot: dict[str, Any]) -> str:
        current = recent_snapshot.get("current_month", {})
        latest_month = recent_snapshot.get("latest_month")
        if not latest_month:
            return "目前尚無可用月份資料，因此暫時無法生成最新月份分析摘要。"

        revenue_extremes = dashboard_snapshot.get("revenue_extremes", {})
        inventory_extremes = dashboard_snapshot.get("inventory_extremes", {})
        anomalies = dashboard_snapshot.get("anomalies", [])

        parts = [
            f"{latest_month} 為目前最新月份，總營收 {format_number(current.get('revenue'))}、總庫存金額 {format_number(current.get('inventory_amount'))}、總庫存 QTY {format_number(current.get('inventory_qty'), decimals=0)}。"
        ]

        if revenue_extremes:
            parts.append(
                f"本月營收最高平台為 {revenue_extremes.get('max_platform')}（{format_number(revenue_extremes.get('max_value'))}），最低為 {revenue_extremes.get('min_platform')}（{format_number(revenue_extremes.get('min_value'))}）。"
            )
        if inventory_extremes:
            parts.append(
                f"本月庫存金額最高平台為 {inventory_extremes.get('max_platform')}（{format_number(inventory_extremes.get('max_value'))}），最低為 {inventory_extremes.get('min_platform')}（{format_number(inventory_extremes.get('min_value'))}）。"
            )
        if anomalies:
            anomaly = anomalies[0]
            parts.append(
                f"本月最值得優先追蹤的異常為 {anomaly.get('平台') or '整體'} / {anomaly.get('異常類型')}，訊號值 {format_number(anomaly.get('訊號'))}。"
            )

        return " ".join(parts)

    def _build_dashboard_snapshot_v2(self, recent_snapshot: dict[str, Any]) -> dict[str, Any]:
        latest_month = recent_snapshot.get("latest_month")
        if not latest_month:
            return {
                "latest_month": None,
                "revenue_extremes": {"max": None, "min": None},
                "inventory_extremes": {"max": None, "min": None},
                "anomalies": [],
                "anomaly_count": 0,
            }

        platform_month = self.toolbox.get_metric_table("platform_monthly", QueryFilters(month=latest_month))
        anomalies = self.toolbox.get_anomalies(top_n=10, filters=QueryFilters(month=latest_month))

        anomaly_preview_raw = sorted(
            anomalies,
            key=lambda item: abs(float(item.get(COL_ANOMALY_SIGNAL, 0) or 0)),
            reverse=True,
        )[:3]

        return {
            "latest_month": latest_month,
            "revenue_extremes": self._build_platform_extremes_v2(platform_month, COL_REVENUE),
            "inventory_extremes": self._build_platform_extremes_v2(platform_month, COL_INV_AMOUNT),
            "anomalies": [
                {
                    "month": item.get(COL_MONTH),
                    "platform": item.get(COL_PLATFORM),
                    "group_code": item.get(COL_GROUP_CODE),
                    "type": item.get(COL_ANOMALY_TYPE),
                    "reason": item.get(COL_ANOMALY_REASON),
                    "signal": self._coerce_number(item.get(COL_ANOMALY_SIGNAL)),
                }
                for item in anomaly_preview_raw
            ],
            "anomaly_count": len(anomalies),
        }

    @staticmethod
    def _build_platform_extremes_v2(df: pd.DataFrame, value_column: str) -> dict[str, Any]:
        if df.empty or value_column not in df.columns or COL_PLATFORM not in df.columns:
            return {"max": None, "min": None}

        grouped = (
            df.groupby(COL_PLATFORM, as_index=False)[value_column]
            .sum(min_count=1)
            .sort_values(value_column, ascending=False)
            .reset_index(drop=True)
        )
        if grouped.empty:
            return {"max": None, "min": None}

        max_row = grouped.iloc[0]
        min_row = grouped.iloc[-1]
        return {
            "max": {
                "platform": max_row.get(COL_PLATFORM),
                "value": MultiAgentAssistant._coerce_number(max_row.get(value_column)),
            },
            "min": {
                "platform": min_row.get(COL_PLATFORM),
                "value": MultiAgentAssistant._coerce_number(min_row.get(value_column)),
            },
        }

    @staticmethod
    def _build_latest_month_analysis_v2(recent_snapshot: dict[str, Any], dashboard_snapshot: dict[str, Any]) -> str:
        current = recent_snapshot.get("current_month", {})
        latest_month = recent_snapshot.get("latest_month")
        if not latest_month:
            return "目前尚未載入可用資料，因此還無法生成最新月份分析。"

        parts = [
            (
                f"{latest_month} 的整體表現中，營收為 {format_number(current.get('revenue'))}，"
                f"庫存金額為 {format_number(current.get('inventory_amount'))}，"
                f"庫存 QTY 為 {format_number(current.get('inventory_qty'), decimals=0)}。"
            )
        ]

        revenue_extremes = dashboard_snapshot.get("revenue_extremes", {})
        inventory_extremes = dashboard_snapshot.get("inventory_extremes", {})
        revenue_max = revenue_extremes.get("max")
        revenue_min = revenue_extremes.get("min")
        inventory_max = inventory_extremes.get("max")
        inventory_min = inventory_extremes.get("min")

        if revenue_max and revenue_min:
            parts.append(
                f"平台營收以 {revenue_max.get('platform')} 最高，為 {format_number(revenue_max.get('value'))}；"
                f"{revenue_min.get('platform')} 最低，為 {format_number(revenue_min.get('value'))}。"
            )
        if inventory_max and inventory_min:
            parts.append(
                f"平台庫存以 {inventory_max.get('platform')} 最高，為 {format_number(inventory_max.get('value'))}；"
                f"{inventory_min.get('platform')} 最低，為 {format_number(inventory_min.get('value'))}。"
            )

        anomalies = dashboard_snapshot.get("anomalies", [])
        if anomalies:
            lead = anomalies[0]
            parts.append(
                f"目前最需要關注的異常出現在 {lead.get('platform') or '未標示平台'}，"
                f"原因為 {lead.get('reason') or lead.get('type') or '未提供'}，"
                f"訊號值為 {format_number(lead.get('signal'))}。"
            )
        else:
            parts.append("目前最新月份沒有偵測到需要優先處理的異常訊號。")

        return " ".join(parts)

    # -------------------------------------------------------------------------
    # Shared Data Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _lookup_metric_value(
        df: pd.DataFrame,
        month: str | None,
        column: str,
        *,
        decimals: int = 2,
    ) -> float | int | None:
        if df.empty or not month or "月份" not in df.columns or column not in df.columns:
            return None

        matched = df[df["月份"].astype(str) == str(month)]
        if matched.empty:
            return None
        return MultiAgentAssistant._coerce_number(matched.iloc[-1].get(column), decimals=decimals)

    @staticmethod
    def _sum_metric_values(
        df: pd.DataFrame,
        months: list[str],
        column: str,
        *,
        decimals: int = 2,
    ) -> float | int | None:
        if df.empty or not months or "月份" not in df.columns or column not in df.columns:
            return None

        matched = df[df["月份"].astype(str).isin([str(month) for month in months])]
        if matched.empty:
            return None
        return MultiAgentAssistant._coerce_number(matched[column].sum(min_count=1), decimals=decimals)

    @staticmethod
    def _coerce_number(value: Any, *, decimals: int = 2) -> float | int | None:
        if pd.isna(value):
            return None
        number = float(value)
        if decimals == 0:
            return int(round(number))
        return round(number, decimals)

    # -------------------------------------------------------------------------
    # Enterprise Analysis Pipeline
    #   1. Question Understanding / Routing
    #   2. Tool Planning
    #   3. Evidence Execution
    #   4. Answer Contract Generation
    #   5. Response Assembly
    #   6. Logging
    # -------------------------------------------------------------------------
    def answer(self, question: str) -> dict[str, Any]:
        self.logger.info("Received question: %s", question)
        routing = self._run_question_understanding(question)
        task_profile = build_task_profile(question, routing)
        answer_plan = build_answer_plan(task_profile, routing)
        self._apply_phase8a_answer_plan_hints(routing, task_profile)
        self.logger.info(
            "phase8a.plan task_family=%s answer_style=%s primary_tools=%s",
            task_profile.task_family,
            task_profile.answer_style,
            answer_plan.primary_tools,
        )

        if routing.question_type == "overview":
            self.logger.info("tool_execution.start path=overview domain_count=0")
            self.logger.info("tool_execution.done path=overview domain_count=0")
            self.logger.info("answer_generation.start path=overview")
            contract, summary_payload = self._build_overview_contract(routing)
            contract["task_profile"] = asdict(task_profile)
            contract["answer_plan"] = asdict(answer_plan)
            self.logger.info("answer_generation.done answer_type=%s", contract["answer_type"])
            return self._build_response_payload(
                routing=routing,
                contract=contract,
                domain_results=[],
                project_summary=summary_payload,
                task_profile=task_profile,
                answer_plan=answer_plan,
            )

        if routing.question_type == "data_quality":
            self.logger.info("tool_execution.start path=data_quality domain_count=0")
            self.logger.info("tool_execution.done path=data_quality domain_count=0")
            self.logger.info("answer_generation.start path=data_quality")
            contract = self._build_data_quality_contract(routing, task_profile=task_profile, answer_plan=answer_plan)
            contract = self._maybe_rewrite_answer_contract(question, contract)
            self.logger.info("answer_generation.done answer_type=%s", contract["answer_type"])
            return self._build_response_payload(
                routing=routing,
                contract=contract,
                domain_results=[],
                task_profile=task_profile,
                answer_plan=answer_plan,
            )

        domain_results = self._execute_domain_agents(question, routing)
        self.logger.info("answer_generation.start path=standard")
        contract = build_answer_contract(
            request_id=self.request_id,
            question=question,
            routing=routing,
            domain_results=domain_results,
            toolbox=self.toolbox,
            task_profile=task_profile,
            answer_plan=answer_plan,
        )
        contract = self._maybe_rewrite_answer_contract(question, contract)
        self.logger.info(
            "answer_generation.done answer_type=%s evidence=%s tools=%s",
            contract["answer_type"],
            len(contract.get("evidence", [])),
            len(contract.get("tools_used", [])),
        )
        return self._build_response_payload(
            routing=routing,
            contract=contract,
            domain_results=domain_results,
            task_profile=task_profile,
            answer_plan=answer_plan,
        )

    # -------------------------------------------------------------------------
    # Question Understanding / Routing
    # -------------------------------------------------------------------------
    def _run_question_understanding(self, question: str) -> RoutingDecision:
        self.logger.info("question_understanding.start question=%s", question)
        routing = self._plan_and_route(question)
        if self.use_llm_planner:
            planning = self._try_llm_tool_plan(question)
            if planning.ok and planning.plan is not None:
                routing = self._merge_llm_tool_plan(question, routing, planning.plan)
            else:
                self.logger.info(
                    "llm_planner.fallback reason=%s error=%s",
                    planning.fallback_reason,
                    planning.error,
                )
        self._apply_implicit_latest_month_filter(routing)
        self.logger.info(
            "question_understanding.done question_type=%s domains=%s intents=%s filters=%s subtasks=%s",
            routing.question_type,
            routing.domains,
            routing.intents,
            asdict(routing.filters),
            routing.subtasks,
        )
        return routing

    def _try_llm_tool_plan(self, question: str) -> LLMPlanningResult:
        self.logger.info("llm_planner.start question=%s", question)
        return self.llm_planner.plan_question(question, self.llm_client)

    @staticmethod
    def _apply_phase8a_answer_plan_hints(routing: RoutingDecision, task_profile: TaskProfile) -> None:
        task_family = task_profile.task_family
        planned_tools = list(getattr(routing, "planned_tools", []))
        domains = list(getattr(routing, "domains", []))

        if task_family == "cross_section_compare":
            domains.append("financial")
            planned_tools.extend(["get_platform_performance_snapshot", "get_platform_ratios", "get_anomalies"])
        elif task_family == "performance_assessment":
            domains.append("financial")
            planned_tools.extend(["get_platform_performance_snapshot", "get_inventory_turnover_proxy", "get_platform_ratios", "get_anomalies"])
        elif task_family == "time_compare":
            domains.append("sales")
            planned_tools.extend(["get_yoy_mom_breakdown(revenue)", "get_contribution_analysis(revenue)"])

        routing.domains = list(dict.fromkeys(domain for domain in domains if domain))
        routing.planned_tools = list(dict.fromkeys(tool for tool in planned_tools if tool))

    def _merge_llm_tool_plan(
        self,
        question: str,
        fallback_routing: RoutingDecision,
        plan: ToolPlan,
    ) -> RoutingDecision:
        merged_answer_strategy = self._planner_answer_strategy(plan, fallback_routing)
        merged_object_dimension = self.llm_planner._suggest_object_dimension(plan) or fallback_routing.object_dimension
        merged_domains = plan.domains or fallback_routing.domains
        merged_intents = [plan.question_type] if plan.question_type not in {"overview", "data_quality"} else fallback_routing.intents
        merged_warnings = list(fallback_routing.warnings)
        if plan.unsupported_reason:
            merged_warnings.append(plan.unsupported_reason)
        merged_subtasks = list(fallback_routing.subtasks) or ["使用 LLM 規劃的工具組合執行 deterministic analysis。"]
        if not merged_subtasks:
            merged_subtasks = ["使用 LLM 規劃的工具組合執行 deterministic analysis。"]

        merged = RoutingDecision(
            question=question,
            question_type=plan.question_type if plan.question_type != "unsupported" else fallback_routing.question_type,
            intents=merged_intents,
            domains=merged_domains,
            filters=fallback_routing.filters,
            object_dimension=merged_object_dimension,
            subtasks=merged_subtasks,
            warnings=list(dict.fromkeys(merged_warnings)),
            business_question_type=fallback_routing.business_question_type,
            kpi_lenses=fallback_routing.kpi_lenses,
            answer_strategy=merged_answer_strategy,
            planned_tools=self.llm_planner.materialize_tools(plan),
            planning_source="llm_planner",
            requires_limitations=plan.requires_limitations,
        )
        self.logger.info(
            "llm_planner.done question_type=%s domains=%s tools=%s",
            merged.question_type,
            merged.domains,
            merged.planned_tools,
        )
        return merged

    @staticmethod
    def _planner_answer_strategy(plan: ToolPlan, fallback_routing: RoutingDecision) -> str:
        if plan.answer_mode in {"ranking", "trend", "comparison", "risk", "diagnosis", "chart", "overview", "data_quality"}:
            return plan.answer_mode
        if plan.answer_mode == "unsupported":
            return fallback_routing.answer_strategy or fallback_routing.question_type
        if plan.answer_mode == "briefing":
            return fallback_routing.answer_strategy or "diagnosis"
        return fallback_routing.answer_strategy or fallback_routing.question_type

    def _apply_implicit_latest_month_filter(self, routing: RoutingDecision) -> None:
        if routing.filters.month:
            return
        lowered = routing.question.lower()
        asks_latest_month = any(
            token in routing.question for token in ["最新月份", "最新月", "本月", "當月"]
        ) or any(token in lowered for token in ["latest month", "current month", "this month"])
        if not asks_latest_month:
            return
        coverage = self.toolbox.get_data_coverage()
        months = coverage.get("months", [])
        if months:
            routing.filters.month = months[-1]

    # -------------------------------------------------------------------------
    # Tool Planning / Evidence Execution
    # -------------------------------------------------------------------------
    def _execute_domain_agents(self, question: str, routing: RoutingDecision) -> list[DomainResult]:
        self.logger.info("tool_execution.start path=standard domains=%s", routing.domains)
        domain_results: list[DomainResult] = []
        for domain in routing.domains:
            agent = self.agents.get(domain)
            if agent is None:
                self.logger.warning("No agent registered for domain=%s", domain)
                continue
            self.logger.info("Dispatching subtask to domain=%s", domain)
            domain_results.append(agent.handle(question, routing))
        self.logger.info("tool_execution.done path=standard domain_results=%s", len(domain_results))
        return domain_results

    # -------------------------------------------------------------------------
    # Answer Contract Generation
    # -------------------------------------------------------------------------
    def _build_overview_contract(self, routing: RoutingDecision) -> tuple[dict[str, Any], dict[str, Any]]:
        summary_payload = self.summarize_project()
        contract = {
            "request_id": self.request_id,
            "answer_type": "overview",
            "answer": self._compose_overview_answer(summary_payload).split("\n\n", 1)[-1],
            "evidence": [],
            "tools_used": ["get_data_coverage", "get_mapping_summary", "get_tool_capability_matrix"],
            "data_scope": {
                "question_type": routing.question_type,
                "domains": routing.domains,
                "filters": asdict(routing.filters),
                "available_months": summary_payload["project_overview"]["months"],
                "latest_month": summary_payload["recent_snapshot"]["latest_month"],
                "supported_domains": summary_payload["project_overview"]["supported_domains"],
            },
            "limitations": [
                "總覽回答只整理目前已載入資料與工具能力，未逐題展開分析。",
            ],
            "suggested_followups": [
                "請指定月份、平台或新事業群，進一步做營收或庫存分析。",
                "請直接詢問風險、趨勢或圖表需求。",
            ],
            "display_blocks": {
                "headline": "目前可先從桌面與手機版分析工作台查看最新月份摘要、圖表與風險訊號。",
                "key_observations": [
                    "目前支援營收、庫存、財務 proxy、異常、資料品質與圖表分析。",
                    "如需深入分析，請指定月份、平台或新事業群。",
                ],
                "table": None,
                "limitations": [
                    "總覽回答只整理目前已載入資料與工具能力，未逐題展開分析。",
                ],
            },
        }
        return contract, summary_payload

    def _build_data_quality_contract(
        self,
        routing: RoutingDecision,
        *,
        task_profile: TaskProfile | None = None,
        answer_plan: AnswerPlan | None = None,
    ) -> dict[str, Any]:
        return build_data_quality_answer_contract(
            request_id=self.request_id,
            routing=routing,
            toolbox=self.toolbox,
            context=self.context,
            task_profile=task_profile,
            answer_plan=answer_plan,
        )

    def _maybe_rewrite_answer_contract(self, question: str, contract: dict[str, Any]) -> dict[str, Any]:
        if not self.use_llm_rewriter:
            return contract

        self.logger.info("llm_rewriter.start answer_type=%s", contract.get("answer_type"))
        rewrite_request = build_rewrite_request(question, contract)
        rewrite_result = self.llm_rewriter.rewrite(rewrite_request, self.llm_client)
        if rewrite_result.ok and rewrite_result.validation_passed:
            rewritten_contract = dict(contract)
            rewritten_contract["answer"] = rewrite_result.rewritten_answer
            self.logger.info("llm_rewriter.done")
            return rewritten_contract

        self.logger.info(
            "llm_rewriter.fallback reason=%s violations=%s",
            rewrite_result.fallback_reason,
            rewrite_result.violations,
        )
        return contract

    # -------------------------------------------------------------------------
    # Response Assembly
    # -------------------------------------------------------------------------
    def _build_routing_payload(self, routing: RoutingDecision) -> dict[str, Any]:
        return {
            "question": routing.question,
            "question_type": routing.question_type,
            "intents": routing.intents,
            "domains": routing.domains,
            "filters": asdict(routing.filters),
            "subtasks": routing.subtasks,
            "warnings": routing.warnings,
            "business_question_type": routing.business_question_type,
            "kpi_lenses": routing.kpi_lenses,
            "answer_strategy": routing.answer_strategy,
        }

    def _build_response_payload(
        self,
        *,
        routing: RoutingDecision,
        contract: dict[str, Any],
        domain_results: list[DomainResult],
        project_summary: dict[str, Any] | None = None,
        task_profile: TaskProfile | None = None,
        answer_plan: AnswerPlan | None = None,
    ) -> dict[str, Any]:
        response = {
            "request_id": self.request_id,
            "routing": self._build_routing_payload(routing),
            "summary": render_answer_contract(self.request_id, contract),
            "answer_contract": contract,
            "domain_results": [asdict(result) for result in domain_results],
        }
        if task_profile is not None:
            response["task_profile"] = asdict(task_profile)
        if answer_plan is not None:
            response["answer_plan"] = asdict(answer_plan)
        if project_summary is not None:
            response["project_summary"] = project_summary
        self.logger.info("response_assembly.done domain_results=%s", len(domain_results))
        return response

    # Detailed routing implementation retained as a dedicated layer so the
    # public answer() path reads like an enterprise analysis pipeline.
    def _plan_and_route(self, question: str) -> RoutingDecision:
        fallback = self._fallback_route(question)
        self.logger.info("Fallback routing prepared: %s", fallback)
        business_profile = classify_business_question(question)
        if business_profile.question_type != "query" or business_profile.domains:
            routing = self._routing_from_business_profile(question, business_profile, fallback.filters)
            self.logger.info(
                "Business profile routing selected question_type=%s domains=%s lenses=%s",
                routing.question_type,
                routing.domains,
                routing.kpi_lenses,
            )
            return routing

        lowered = question.lower()
        system_prompt = (
            "You are the main orchestration agent for a multi-agent data assistant. "
            "Classify the user question, decide which domains are needed, and decompose it into subtasks. "
            "Return JSON only."
        )
        user_prompt = (
            "Available domains: sales, inventory, financial, association, chart.\n"
            "Question types: overview, single_domain, cross_domain, ranking, explanation, diagnosis, query.\n"
            f"User question: {question}\n"
            f"Detected filters from deterministic parser: {json.dumps(asdict(fallback.filters), ensure_ascii=False)}\n"
            f"Deterministic routing baseline: {json.dumps({'question_type': fallback.question_type, 'intents': fallback.intents, 'domains': fallback.domains}, ensure_ascii=False)}\n"
            f"Tool capability matrix: {json.dumps(self.capability_matrix, ensure_ascii=False)}\n"
            "Do not plan subtasks that depend on unavailable capabilities. If a capability is unavailable, prefer a limitation-aware or fallback subtask.\n"
            'Return JSON with keys question_type, intents, domains, subtasks.'
        )
        result = self.llm_client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.0)
        if not result.ok or not result.data:
            self.logger.info("Main agent planning fallback enabled because Ollama returned no JSON")
            return fallback

        data = result.data
        allowed_question_types = {"overview", "single_domain", "cross_domain", "ranking", "explanation", "diagnosis", "query"}
        llm_question_type = data.get("question_type")
        if not isinstance(llm_question_type, str) or llm_question_type not in allowed_question_types:
            question_type = fallback.question_type
        elif fallback.question_type != "overview" and llm_question_type == "overview":
            question_type = fallback.question_type
        else:
            question_type = llm_question_type

        llm_intents = [item for item in data.get("intents", []) if isinstance(item, str)]
        intents = fallback.intents
        if llm_intents and (set(llm_intents) & set(fallback.intents) or fallback.question_type == "overview"):
            intents = list(dict.fromkeys(fallback.intents + llm_intents))

        llm_domains = [item for item in data.get("domains", []) if item in self.agents]
        domains = fallback.domains
        if fallback.question_type == "cross_domain":
            domains = list(dict.fromkeys(fallback.domains + llm_domains)) or fallback.domains
        elif fallback.question_type == "overview":
            domains = []
        elif llm_domains and set(llm_domains).issuperset(set(fallback.domains)):
            domains = fallback.domains

        llm_subtasks = [item for item in data.get("subtasks", []) if isinstance(item, str)]
        subtasks = fallback.subtasks
        if llm_subtasks and domains:
            subtasks = llm_subtasks

        if self._is_pure_financial_proxy_question(question, lowered):
            question_type = "diagnosis" if question_type == "cross_domain" else question_type
            intents = list(dict.fromkeys([*intents, "financial"]))
            domains = ["financial"]
            subtasks = self._build_subtasks(domains, question_type, fallback.filters)
        elif self._is_explicit_chart_request(question, lowered):
            question_type = "single_domain"
            intents = list(dict.fromkeys([*intents, "chart"]))
            domains = ["chart"]
            subtasks = self._build_subtasks(domains, question_type, fallback.filters)

        return RoutingDecision(
            question=question,
            question_type=question_type,
            intents=list(dict.fromkeys(intents)),
            domains=list(dict.fromkeys(domains)),
            filters=fallback.filters,
            object_dimension=fallback.object_dimension,
            subtasks=subtasks,
            warnings=fallback.warnings,
        )

    def _routing_from_business_profile(
        self,
        question: str,
        profile: BusinessQuestionProfile,
        filters: QueryFilters,
    ) -> RoutingDecision:
        domains: list[str] = []
        for domain in profile.domains:
            if domain == "chart" or self.context.supported_domains.get(domain, True):
                domains.append(domain)

        if profile.needs_chart and "chart" not in domains:
            domains.append("chart")

        if profile.question_type in {"overview", "data_quality"}:
            domains = []

        fields = profile_to_routing_fields(profile)
        return RoutingDecision(
            question=question,
            question_type=profile.question_type,
            intents=list(dict.fromkeys(profile.intents)),
            domains=list(dict.fromkeys(domains)),
            filters=filters,
            object_dimension=profile.object_dimension,
            subtasks=self._build_business_subtasks(profile, filters),
            warnings=profile.warnings,
            business_question_type=fields["business_question_type"],
            kpi_lenses=list(fields["kpi_lenses"]),
            answer_strategy=str(fields["answer_strategy"]),
        )

    def _build_business_subtasks(self, profile: BusinessQuestionProfile, filters: QueryFilters) -> list[str]:
        scope_text = []
        if filters.month:
            scope_text.append(f"月份 {filters.month}")
        if filters.platform:
            scope_text.append(f"平台 {filters.platform}")
        if filters.group_code:
            scope_text.append(f"新事業群 {filters.group_code}")
        scope_suffix = f"（{' / '.join(scope_text)}）" if scope_text else ""

        lens_text = "、".join(lens.label for lens in profile.kpi_lenses) or "既有分析指標"
        task_map = {
            "overview": "整理目前資料與分析能力總覽",
            "trend": f"依 {lens_text} 檢查趨勢與最近變化{scope_suffix}",
            "ranking": f"依 {lens_text} 建立排名並先給直接答案{scope_suffix}",
            "comparison": f"比較指定對象在 {lens_text} 的差異{scope_suffix}",
            "diagnosis": f"使用現有證據診斷變化原因，並標示資料限制{scope_suffix}",
            "risk": f"整理異常與高風險清單{scope_suffix}",
            "chart": f"產生符合問題的圖表資料與表格摘要{scope_suffix}",
            "data_quality": "檢查資料覆蓋、mapping、pipeline 警告與錯誤",
            "decision": f"整理管理優先處理清單與理由{scope_suffix}",
        }
        return [task_map.get(profile.question_type, f"依 {lens_text} 回答問題{scope_suffix}")]

    def _fallback_route(self, question: str) -> RoutingDecision:
        lowered = question.lower()
        if self._is_overview_question(question, lowered):
            return RoutingDecision(
                question=question,
                question_type="overview",
                intents=["overview"],
                domains=[],
                filters=QueryFilters(),
                object_dimension=None,
                subtasks=["Summarize current project capabilities and limitations."],
                warnings=[],
            )

        intents: list[str] = []
        domains: list[str] = []
        question_type = "query"

        ratio_or_risk = any(token in question for token in ["比值", "異常", "風險", "診斷"]) or "ratio" in lowered
        chart_like = any(token in question for token in ["圖", "圖表", "畫圖", "製圖", "視覺化", "折線圖", "長條圖"]) or any(
            token in lowered for token in ["chart", "plot", "graph", "visual"]
        )
        trend_or_ranking = any(
            token in question for token in ["趨勢", "走勢", "變化", "排名", "排行", "最好", "最高", "最低", "為什麼"]
        ) or any(token in lowered for token in ["trend", "rank", "ranking", "why", "diagnosis"])
        sales_like = any(token in question for token in ["營收", "銷售", "賣得", "賣最好", "賣很好", "銷量"]) or any(
            token in lowered for token in ["revenue", "sales", "sell", "selling"]
        )
        inventory_like = any(token in question for token in ["庫存", "QTY", "金額", "HQBU", "存貨"]) or any(
            token in lowered for token in ["inventory", "stock"]
        )
        finance_like = any(token in question for token in ["財務", "比值", "異常", "風險"]) or any(
            token in lowered for token in ["finance", "ratio", "anomaly", "risk"]
        )
        association_like = any(token in question for token in ["關聯", "相關"]) or any(
            token in lowered for token in ["association", "correlation", "basket", "co-occurrence"]
        )
        explicit_chart_request = self._is_explicit_chart_request(question, lowered)

        pure_financial_proxy = self._is_pure_financial_proxy_question(
            question,
            lowered,
            sales_like=sales_like,
            inventory_like=inventory_like,
            finance_like=finance_like,
            ratio_or_risk=ratio_or_risk,
            trend_or_ranking=trend_or_ranking,
            association_like=association_like,
        )

        if explicit_chart_request:
            intents.append("chart")
            domains.append("chart")
        elif pure_financial_proxy:
            intents.append("financial")
            domains.append("financial")
        if sales_like and not pure_financial_proxy and not explicit_chart_request:
            intents.append("revenue")
            domains.append("sales")
        if inventory_like and not pure_financial_proxy and not explicit_chart_request:
            intents.append("inventory")
            domains.append("inventory")
        if finance_like and not explicit_chart_request:
            intents.append("financial")
            domains.append("financial")
        if association_like and not explicit_chart_request:
            intents.append("association")
            domains.append("association")
        if chart_like and not explicit_chart_request:
            intents.append("chart")
            domains.append("chart")

        if sales_like and inventory_like and question_type != "overview" and not pure_financial_proxy:
            domains = list(dict.fromkeys(domains + ["sales", "inventory", "financial"]))
            intents = list(dict.fromkeys(intents + ["revenue", "inventory", "financial"]))

        if not domains:
            supported = [domain for domain, enabled in self.context.supported_domains.items() if enabled]
            domains = supported
            intents = ["overview"]
            question_type = "overview"

        if len(domains) > 1:
            question_type = "cross_domain"
        elif any(token in question for token in ["排名", "排行", "最好", "最高", "最低"]) or "ranking" in lowered:
            question_type = "ranking"
        elif any(token in question for token in ["為什麼", "原因", "怎麼解釋", "診斷"]) or "why" in lowered:
            question_type = "diagnosis"
        elif trend_or_ranking:
            question_type = "single_domain"
        elif ratio_or_risk:
            question_type = "diagnosis"

        filters = QueryFilters(
            month=self._extract_month(question),
            platform=self._extract_platform(question),
            group_code=self._extract_group_code(question),
        )
        warnings: list[str] = []
        if "financial" in domains and not self.context.supported_domains.get("financial"):
            warnings.append("目前 financial 只能提供營收/庫存代理指標分析，無法直接回答完整財報問題。")
        if any(token in question for token in ["產品", "商品", "SKU"]) and not filters.platform and not filters.group_code:
            warnings.append("目前資料沒有明確產品/SKU 維度，系統會先以現有事業群、平台與月份層級做近似分析。")

        subtasks = self._build_subtasks(domains, question_type, filters)
        return RoutingDecision(
            question=question,
            question_type=question_type,
            intents=list(dict.fromkeys(intents)),
            domains=list(dict.fromkeys(domains)),
            filters=filters,
            object_dimension=self._infer_object_dimension(question, lowered),
            subtasks=subtasks,
            warnings=warnings,
        )

    def _build_subtasks(self, domains: list[str], question_type: str, filters: QueryFilters) -> list[str]:
        scope_text = []
        if filters.month:
            scope_text.append(f"月份 {filters.month}")
        if filters.platform:
            scope_text.append(f"平台 {filters.platform}")
        if filters.group_code:
            scope_text.append(f"新事業群 {filters.group_code}")
        scope_suffix = f"（{' / '.join(scope_text)}）" if scope_text else ""

        task_map = {
            "sales": f"檢查營收趨勢、排行與變化{scope_suffix}",
            "inventory": f"檢查庫存金額與 QTY 變化{scope_suffix}",
            "financial": f"檢查營收/庫存代理指標與異常{scope_suffix}",
            "association": f"檢查相關分析或 association fallback{scope_suffix}",
            "chart": f"產出適合前端渲染的圖表資料與圖檔{scope_suffix}",
        }
        tasks = [task_map[domain] for domain in domains if domain in task_map]
        if question_type == "cross_domain":
            tasks.append("整合跨領域結果並整理可能原因與限制")
        return tasks

    @staticmethod
    def _infer_object_dimension(question: str, lowered: str) -> str | None:
        if any(token in question for token in ["平台", "平臺"]) or "platform" in lowered:
            return "platform"
        if any(token in question for token in ["新事業群", "事業群"]) or "group" in lowered:
            return "business_group"
        if any(token in question for token in ["月份", "本月", "最新月份", "最新月"]) or "month" in lowered:
            return "month"
        return None

    # Legacy synthesis helpers are intentionally retained for debugging and
    # compatibility with older orchestration experiments. The stable Phase 2+
    # answer path now relies on answer_contract.py and _build_response_payload().
    def _synthesize_final_answer(
        self,
        question: str,
        routing: RoutingDecision,
        domain_results: list[DomainResult],
    ) -> str:
        if routing.domains == ["chart"] and len(domain_results) == 1:
            return self._compose_chart_answer(domain_results[0], routing)

        evidence_first_answer = compose_evidence_first_answer(
            request_id=self.request_id,
            question=question,
            routing=routing,
            domain_results=domain_results,
            toolbox=self.toolbox,
            context=self.context,
        )
        if evidence_first_answer:
            return evidence_first_answer

        system_prompt = (
            "You are the main answer synthesizer. "
            "Combine child-agent outputs into a concise Traditional Chinese answer for an enterprise analytics product. "
            "Do not use markdown headings, emoji labels, or verbose template sections like direct answer/evidence. "
            f"{LLM_FIELD_BOUNDARY_PROMPT}"
        )
        user_prompt = (
            f"Question: {question}\n"
            f"Routing: {json.dumps({'question_type': routing.question_type, 'domains': routing.domains, 'filters': asdict(routing.filters), 'subtasks': routing.subtasks}, ensure_ascii=False, indent=2)}\n"
            f"Domain results: {json.dumps([asdict(result) for result in domain_results], ensure_ascii=False, indent=2)}\n"
            "Respond in Traditional Chinese. Start with the direct answer supported by evidence. "
            "If the evidence does not contain a field, explicitly say it is unavailable instead of inferring it. "
            "Use short paragraphs plus concise bullets only when genuinely helpful."
        )
        result = self.llm_client.generate(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.1)
        if result.ok and result.text:
            return f"Request ID: {self.request_id}\n\n{result.text.strip()}"
        return self._compose_final_answer_fallback(domain_results, routing)

    def _compose_chart_answer(self, result: DomainResult, routing: RoutingDecision) -> str:
        chart_payload = next(
            (item for item in result.evidence if isinstance(item, dict) and item.get("chart_type") and item.get("chart_key")),
            None,
        )
        image_result = next(
            (item for item in result.evidence if isinstance(item, dict) and item.get("output_path")),
            None,
        )
        table_rows = []
        if chart_payload and chart_payload.get("table_preview"):
            table_rows = chart_payload.get("table_preview", [])
        else:
            table_evidence = next(
                (item for item in result.evidence if isinstance(item, dict) and item.get("table_preview")),
                None,
            )
            if table_evidence:
                table_rows = table_evidence.get("table_preview", [])

        lines = [f"Request ID: {self.request_id}"]
        if chart_payload:
            lines.append(
                f"已依照需求產生 {chart_payload.get('title', chart_payload.get('chart_key'))}，圖型為 {chart_payload.get('chart_type')}。"
            )
            filters = chart_payload.get("filters", {})
            if filters.get("month"):
                lines.append(f"圖表範圍已套用月份 {filters['month']}。")
        else:
            lines.append("目前無法依照指定條件產生圖表。")

        if table_rows:
            preview = table_rows[:6]
            lines.append("對應表格摘要如下：")
            for row in preview:
                parts = [f"{key}={value}" for key, value in row.items()]
                lines.append("- " + "，".join(parts))

        if image_result:
            lines.append(f"圖檔已輸出至 {image_result['output_path']}。")
        if result.warnings:
            lines.extend([f"- {warning}" for warning in result.warnings])
        return "\n\n".join([lines[0], "\n".join(lines[1:]) if len(lines) > 1 else ""])

    def _compose_final_answer_fallback(self, domain_results: list[DomainResult], routing: RoutingDecision) -> str:
        sections = [f"Request ID: {self.request_id}"]
        sections.append(f"Question type: {routing.question_type}")
        sections.append(f"Router domains: {', '.join(routing.domains)}")
        if any(asdict(routing.filters).values()):
            sections.append(f"Filters: {asdict(routing.filters)}")
        if routing.subtasks:
            sections.append("Subtasks:\n- " + "\n- ".join(routing.subtasks))

        for result in domain_results:
            lines = [f"[{result.domain}] status={result.status} confidence={result.confidence}"]
            for finding in result.key_findings:
                lines.append(f"- {finding}")
            for warning in result.warnings:
                lines.append(f"- warning: {warning}")
            sections.append("\n".join(lines))
        return "\n\n".join(sections)

    def _compose_overview_answer(self, summary_payload: dict[str, Any]) -> str:
        overview = summary_payload["project_overview"]
        supported = [domain for domain, enabled in overview["supported_domains"].items() if enabled]
        unsupported = summary_payload["not_directly_supported"]
        month_text = (
            f"{overview['months'][0]} 到 {overview['months'][-1]}"
            if overview["months"]
            else "目前沒有可用月份資料"
        )
        return "\n".join(
            [
                f"Request ID: {self.request_id}",
                "",
                "目前資料可支援的分析如下：",
                f"- 支援 domain: {', '.join(supported)}",
                f"- 資料月份範圍: {month_text}",
                f"- 營收資料筆數: {overview['revenue_rows']}",
                f"- 庫存資料筆數: {overview['inventory_rows']}",
                "- 可直接做營收趨勢、庫存趨勢、群組排行、營收/庫存代理比值、異常偵測、相關分析與圖表輸出。",
                f"- 目前不直接支援: {', '.join(unsupported)}",
            ]
        )

    def _extract_group_code(self, question: str) -> str | None:
        direct = re.search(r"(?:新事業群|事業群代碼)\s*[:：]?\s*(\d+)", question)
        if direct:
            return direct.group(1)

        business_groups = self.context.parsed_mapping.business_group_mapping
        if business_groups.empty:
            return None

        for _, row in business_groups.iterrows():
            name = str(row.get("事業群", "")).strip()
            if name and name in question:
                return str(row.get("事業群代碼"))
        return None

    @staticmethod
    def _is_overview_question(question: str, lowered: str) -> bool:
        overview_keywords = [
            "目前資料可支援哪些分析",
            "目前可以做哪些分析",
            "專案能力",
            "支援哪些分析",
            "有哪些分析能力",
            "project summary",
            "capability",
        ]
        return any(keyword in question for keyword in overview_keywords) or any(keyword in lowered for keyword in ["capability", "project summary"])

    @staticmethod
    def _is_pure_financial_proxy_question(
        question: str,
        lowered: str,
        *,
        sales_like: bool | None = None,
        inventory_like: bool | None = None,
        finance_like: bool | None = None,
        ratio_or_risk: bool | None = None,
        trend_or_ranking: bool | None = None,
        association_like: bool | None = None,
    ) -> bool:
        sales_like = sales_like if sales_like is not None else (
            any(token in question for token in ["營收", "銷售", "賣得", "賣最好", "賣很好", "銷量"])
            or any(token in lowered for token in ["revenue", "sales", "sell", "selling"])
        )
        inventory_like = inventory_like if inventory_like is not None else (
            any(token in question for token in ["庫存", "QTY", "金額", "HQBU", "存貨"])
            or any(token in lowered for token in ["inventory", "stock"])
        )
        finance_like = finance_like if finance_like is not None else (
            any(token in question for token in ["財務", "比值", "異常", "風險"])
            or any(token in lowered for token in ["finance", "ratio", "anomaly", "risk"])
        )
        ratio_or_risk = ratio_or_risk if ratio_or_risk is not None else (
            any(token in question for token in ["比值", "異常", "風險", "診斷"])
            or "ratio" in lowered
        )
        trend_or_ranking = trend_or_ranking if trend_or_ranking is not None else (
            any(token in question for token in ["趨勢", "走勢", "變化", "排名", "排行", "最好", "最高", "最低", "為什麼"])
            or any(token in lowered for token in ["trend", "rank", "ranking", "why", "diagnosis"])
        )
        association_like = association_like if association_like is not None else (
            any(token in question for token in ["關聯", "相關"])
            or any(token in lowered for token in ["association", "correlation", "basket", "co-occurrence"])
        )

        return (
            finance_like
            and ratio_or_risk
            and sales_like
            and inventory_like
            and not association_like
            and not trend_or_ranking
        )

    @staticmethod
    def _is_explicit_chart_request(question: str, lowered: str) -> bool:
        chart_like = any(token in question for token in ["圖", "圖表", "畫圖", "製圖", "視覺化", "折線圖", "長條圖"])
        chart_like = chart_like or any(token in lowered for token in ["chart", "plot", "graph", "visual"])
        explanation_like = any(token in question for token in ["原因", "為什麼", "解釋", "診斷", "異常", "風險"])
        explanation_like = explanation_like or any(token in lowered for token in ["why", "explain", "diagnosis", "anomaly", "risk"])
        return chart_like and not explanation_like

    @staticmethod
    def _extract_month(question: str) -> str | None:
        match = re.search(r"(20\d{2})[-/]?(0[1-9]|1[0-2])", question)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        month_only = re.search(r"(?<!\d)(1[0-2]|0?[1-9])\s*月", question)
        if month_only:
            month = int(month_only.group(1))
            return f"2024-{month:02d}"

        chinese_months = {
            "一月": "2024-01",
            "二月": "2024-02",
            "三月": "2024-03",
            "四月": "2024-04",
            "五月": "2024-05",
            "六月": "2024-06",
            "七月": "2024-07",
            "八月": "2024-08",
            "九月": "2024-09",
            "十月": "2024-10",
            "十一月": "2024-11",
            "十二月": "2024-12",
        }
        for token, month in chinese_months.items():
            if token in question:
                return month

        return None

    @staticmethod
    def _extract_platform(question: str) -> str | None:
        match = re.search(r"GG-(0[1-9]|[1-8][0-9]|9[0-1])", question.upper())
        return match.group(0) if match else None
