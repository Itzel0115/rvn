from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class KpiLens:
    name: str
    label: str
    description: str
    sort_direction: str


@dataclass(frozen=True)
class BusinessQuestionProfile:
    question_type: str
    intents: list[str]
    domains: list[str]
    kpi_lenses: list[KpiLens] = field(default_factory=list)
    object_dimension: str | None = None
    answer_strategy: str = "llm_assisted"
    needs_chart: bool = False
    warnings: list[str] = field(default_factory=list)


KPI_LENSES = {
    "revenue_scale": KpiLens(
        name="revenue_scale",
        label="營收規模",
        description="關注營收絕對值、排名與主力平台/事業群。",
        sort_direction="descending",
    ),
    "revenue_growth": KpiLens(
        name="revenue_growth",
        label="營收成長",
        description="關注月增、衰退與趨勢變化。",
        sort_direction="descending",
    ),
    "inventory_efficiency": KpiLens(
        name="inventory_efficiency",
        label="庫存效率",
        description="關注營收相對庫存的效率 proxy 與弱勢組合。",
        sort_direction="ascending",
    ),
    "risk_anomaly": KpiLens(
        name="risk_anomaly",
        label="風險異常",
        description="關注異常訊號、背離現象與需要追蹤的風險。",
        sort_direction="descending",
    ),
    "overall_health": KpiLens(
        name="overall_health",
        label="整體體質",
        description="綜合營收、庫存與異常觀測整理整體表現。",
        sort_direction="mixed",
    ),
}


OVERVIEW_KEYWORDS = ["overview", "summary", "capability", "project summary", "總覽", "摘要", "專案能力"]
DATA_QUALITY_KEYWORDS = [
    "data quality",
    "coverage",
    "covered",
    "cover",
    "mapping",
    "available month",
    "available months",
    "what months are available",
    "missing",
    "data coverage",
    "資料品質",
    "資料涵蓋",
    "涵蓋",
    "缺失",
    "mapping",
]
CHART_KEYWORDS = ["chart", "plot", "graph", "visual", "圖", "畫", "畫圖", "圖表", "視覺化", "趨勢圖"]
DECISION_KEYWORDS = ["priority", "prioritize", "decision", "next step", "action", "最近狀況", "優先", "下一步", "決策", "要注意"]
COMPARISON_KEYWORDS = ["compare", "comparison", "versus", " vs ", "比較", "對比", "差異"]
RISK_KEYWORDS = ["risk", "anomaly", "anomalies", "warning", "divergence", "risky", "風險", "異常", "警示", "背離"]
DIAGNOSIS_KEYWORDS = ["why", "diagnosis", "explain", "root cause", "為什麼", "原因", "診斷", "根因"]
RANKING_KEYWORDS = ["ranking", "rank", "top", "bottom", "best", "worst", "weakest", "lowest", "highest", "排名", "排行", "最高", "最低"]
TREND_KEYWORDS = ["trend", "growth", "decline", "monthly", "mom", "趨勢", "走勢", "月增", "下降", "上升", "變化"]
PERFORMANCE_WEAKNESS_KEYWORDS = [
    "健康",
    "最健康",
    "最穩",
    "比較穩",
    "表現較佳",
    "表現較好",
    "表現最好",
    "表現較差",
    "表現最差",
    "表現較弱",
    "表現較強",
    "表現不佳",
    "哪個平台表現",
    "表現較差",
    "表現不好",
    "表現最弱",
    "表現差",
    "較弱",
    "最弱",
    "比較差",
    "比較不好",
    "落後",
    "效率差",
    "哪個平台有問題",
    "哪個平台需要注意",
    "哪個平台需要優先注意",
    "需要注意",
    "優先注意",
    "哪個平台狀況不好",
    "needs attention",
    "performing worse",
    "performing poorly",
    "inventory pressure",
    "pressure",
    "庫存壓力",
    "壓力較高",
    "壓力高",
]

REVENUE_KEYWORDS = ["revenue", "sales", "sell", "營收", "銷售"]
INVENTORY_KEYWORDS = ["inventory", "stock", "qty", "庫存", "存貨", "金額", "數量"]
EFFICIENCY_KEYWORDS = ["ratio", "efficiency", "營收/庫存", "庫存/營收", "效率", "週轉", "周轉", "proxy"]
PLATFORM_KEYWORDS = ["platform", "平台", "平臺", "gg-"]
GROUP_KEYWORDS = ["group", "business group", "business unit", "BU", "bu", "新事業群", "事業群", "群組"]
PRODUCT_LINE_KEYWORDS = ["product line", "product_line", "產品線", "五大產品線", "哪個產品線"]
MONTH_KEYWORDS = ["month", "months", "月份", "本月", "最新月份", "最新月", "latest month", "current month"]
LOOKUP_KEYWORDS = ["列出", "顯示", "查詢", "查看", "看一下", "告訴我", "多少", "是多少", "資料", "數據"]
OVERALL_KEYWORDS = ["總體", "整體", "overall", "全部"]


def classify_business_question(question: str) -> BusinessQuestionProfile:
    text = question.strip()
    lowered = text.lower()

    object_dimension = _detect_object_dimension(text, lowered)
    needs_chart = _contains_any(text, lowered, CHART_KEYWORDS)
    kpi_lenses = _detect_kpi_lenses(text, lowered)

    if _is_forecast_question(text, lowered):
        return BusinessQuestionProfile(
            question_type="unsupported",
            intents=["forecast", "unsupported"],
            domains=[],
            kpi_lenses=kpi_lenses,
            object_dimension=object_dimension,
            answer_strategy="unsupported",
            warnings=["目前系統尚未納入預測模型、訂單、出貨、價格或市場需求資料，不能直接預測未來月份。"],
        )

    if _is_parent_child_drilldown_question(text):
        return BusinessQuestionProfile(
            question_type="comparison",
            intents=["parent_child_drilldown", "performance"],
            domains=["financial"],
            kpi_lenses=[KPI_LENSES["inventory_efficiency"], KPI_LENSES["overall_health"]],
            object_dimension="product_line_5",
            answer_strategy="parent_child_drilldown",
            needs_chart=needs_chart,
        )

    if _is_contribution_question(text, lowered):
        return BusinessQuestionProfile(
            question_type="comparison",
            intents=["contribution_analysis", "comparison"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or [KPI_LENSES["revenue_growth"]],
            object_dimension=object_dimension,
            answer_strategy="contribution_analysis",
            needs_chart=needs_chart,
        )

    if _is_proxy_anomaly_question(text, lowered):
        return BusinessQuestionProfile(
            question_type="risk",
            intents=["metric_relationship_analysis", "risk", "anomaly"],
            domains=["financial"],
            kpi_lenses=[KPI_LENSES["inventory_efficiency"], KPI_LENSES["risk_anomaly"]],
            object_dimension=object_dimension,
            answer_strategy="metric_relationship_analysis",
            needs_chart=needs_chart,
            warnings=["這類問題目前只能用營收與庫存的代理異常訊號回答，不能直接判定根本原因。"],
        )

    if _is_latest_month_platform_summary(text, lowered):
        dimension = object_dimension or "business_group"
        return BusinessQuestionProfile(
            question_type="summary",
            intents=["summary", "performance", "entity"],
            domains=["financial"],
            kpi_lenses=[
                KPI_LENSES["revenue_scale"],
                KPI_LENSES["inventory_efficiency"],
                KPI_LENSES["overall_health"],
                KPI_LENSES["risk_anomaly"],
            ],
            object_dimension=dimension,
            answer_strategy="latest_month_entity_summary",
            needs_chart=needs_chart,
        )

    if _is_entity_time_series_question(text, lowered):
        return BusinessQuestionProfile(
            question_type="trend",
            intents=["entity_time_series", "trend"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or _default_trend_lenses(text, lowered),
            object_dimension=object_dimension,
            answer_strategy="entity_time_series",
            needs_chart=needs_chart,
        )

    if _is_overall_trend_question(text, lowered, object_dimension):
        return BusinessQuestionProfile(
            question_type="trend",
            intents=["overall_trend_analysis", "trend"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or _default_trend_lenses(text, lowered),
            object_dimension="overall",
            answer_strategy="overall_trend_analysis",
            needs_chart=needs_chart,
        )

    if _is_entity_trend_comparison_question(text, lowered, object_dimension):
        return BusinessQuestionProfile(
            question_type="trend",
            intents=["entity_trend_comparison", "trend"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or _default_trend_lenses(text, lowered),
            object_dimension=object_dimension or "business_group",
            answer_strategy="entity_trend_comparison",
            needs_chart=needs_chart,
        )


    if _is_single_month_all_entity_table_question(text, lowered, object_dimension):
        is_compare = _contains_any(text, lowered, COMPARISON_KEYWORDS)
        return BusinessQuestionProfile(
            question_type="comparison" if is_compare else "query",
            intents=["cross_section_compare", "comparison"] if is_compare else ["entity_month_table_lookup", "metric_lookup"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or _default_table_lenses(text, lowered),
            object_dimension=object_dimension,
            answer_strategy="comparison" if is_compare else "entity_month_table_lookup",
            needs_chart=needs_chart,
        )

    if _extract_period_pair(text):
        return BusinessQuestionProfile(
            question_type="comparison",
            intents=["period_pair_compare", "comparison"],
            domains=["sales"],
            kpi_lenses=kpi_lenses or [KPI_LENSES["revenue_scale"]],
            object_dimension=object_dimension,
            answer_strategy="period_pair_compare",
            needs_chart=needs_chart,
        )

    if _contains_any(text, lowered, DATA_QUALITY_KEYWORDS):
        return BusinessQuestionProfile(
            question_type="data_quality",
            intents=["data_quality"],
            domains=[],
            object_dimension=object_dimension,
            answer_strategy="data_quality",
        )

    if _contains_any(text, lowered, OVERVIEW_KEYWORDS):
        return BusinessQuestionProfile(
            question_type="overview",
            intents=["overview"],
            domains=[],
            object_dimension=object_dimension,
            answer_strategy="overview",
        )

    if needs_chart and not (
        _contains_any(text, lowered, RISK_KEYWORDS) or _contains_any(text, lowered, DIAGNOSIS_KEYWORDS)
    ):
        return BusinessQuestionProfile(
            question_type="chart",
            intents=["chart"],
            domains=["chart"],
            kpi_lenses=kpi_lenses,
            object_dimension=object_dimension,
            answer_strategy="chart",
            needs_chart=True,
        )

    if _is_performance_weakness_question(text, lowered, object_dimension):
        return BusinessQuestionProfile(
            question_type="performance_weakness",
            intents=["performance_weakness", "risk", "performance"],
            domains=["financial"],
            kpi_lenses=[KPI_LENSES["inventory_efficiency"], KPI_LENSES["risk_anomaly"]],
            object_dimension="business_group" if object_dimension == "platform" else object_dimension,
            answer_strategy="performance_weakness",
            needs_chart=needs_chart,
        )

    if _contains_any(text, lowered, DECISION_KEYWORDS):
        return BusinessQuestionProfile(
            question_type="decision",
            intents=["decision", "risk", "performance"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or [KPI_LENSES["overall_health"]],
            object_dimension=object_dimension,
            answer_strategy="decision",
            needs_chart=needs_chart,
        )

    if _is_comparison(text, lowered):
        return BusinessQuestionProfile(
            question_type="comparison",
            intents=["comparison", "performance"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or [KPI_LENSES["overall_health"]],
            object_dimension=object_dimension,
            answer_strategy="comparison",
            needs_chart=needs_chart,
        )

    if _contains_any(text, lowered, RISK_KEYWORDS):
        return BusinessQuestionProfile(
            question_type="risk",
            intents=["risk", "anomaly"],
            domains=["financial"],
            kpi_lenses=kpi_lenses or [KPI_LENSES["risk_anomaly"]],
            object_dimension=object_dimension,
            answer_strategy="risk",
            needs_chart=needs_chart,
        )

    if _contains_any(text, lowered, DIAGNOSIS_KEYWORDS):
        return BusinessQuestionProfile(
            question_type="diagnosis",
            intents=["diagnosis"],
            domains=_diagnosis_domains(text, lowered),
            kpi_lenses=kpi_lenses or [KPI_LENSES["overall_health"]],
            object_dimension=object_dimension,
            answer_strategy="diagnosis",
            needs_chart=needs_chart,
        )

    if _contains_any(text, lowered, RANKING_KEYWORDS):
        return BusinessQuestionProfile(
            question_type="ranking",
            intents=["ranking", "performance"],
            domains=_ranking_domains(text, lowered),
            kpi_lenses=kpi_lenses or _default_ranking_lenses(text, lowered),
            object_dimension=object_dimension,
            answer_strategy="ranking",
            needs_chart=needs_chart,
        )

    if _contains_any(text, lowered, TREND_KEYWORDS):
        return BusinessQuestionProfile(
            question_type="trend",
            intents=["trend"],
            domains=_trend_domains(text, lowered),
            kpi_lenses=kpi_lenses or _default_trend_lenses(text, lowered),
            object_dimension=object_dimension,
            answer_strategy="trend",
            needs_chart=needs_chart,
        )

    if kpi_lenses:
        intents = ["metric_query"]
        if _contains_any(text, lowered, LOOKUP_KEYWORDS):
            intents.append("metric_lookup")
        return BusinessQuestionProfile(
            question_type="query",
            intents=intents,
            domains=_domains_for_lenses(kpi_lenses),
            kpi_lenses=kpi_lenses,
            object_dimension=object_dimension,
            answer_strategy="metric_query",
            needs_chart=needs_chart,
        )

    return BusinessQuestionProfile(
        question_type="query",
        intents=["overview"],
        domains=[],
        object_dimension=object_dimension,
        answer_strategy="llm_assisted",
        needs_chart=needs_chart,
    )


def profile_to_routing_fields(profile: BusinessQuestionProfile) -> dict[str, object]:
    return {
        "business_question_type": profile.question_type,
        "kpi_lenses": [lens.name for lens in profile.kpi_lenses],
        "answer_strategy": profile.answer_strategy,
    }


def describe_lenses(lenses: list[KpiLens]) -> list[str]:
    return [f"{lens.label}: {lens.description}" for lens in lenses]


def _contains_any(text: str, lowered: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in lowered for keyword in keywords)


def _is_forecast_question(text: str, lowered: str) -> bool:
    tokens = [
        "forecast",
        "predict",
        "prediction",
        "next month",
        "future",
        "\u4e0b\u500b\u6708",
        "\u4e0b\u6708",
        "\u672a\u4f86",
        "\u9810\u6e2c",
        "\u6703\u4e0d\u6703\u6539\u5584",
        "\u6703\u4e0d\u6703\u4e0b\u964d",
        "\u662f\u5426\u6703\u6210\u9577",
    ]
    return any(token in lowered or token in text for token in tokens)


def _is_latest_month_platform_summary(text: str, lowered: str) -> bool:
    has_platform = any(
        token in lowered or token in text
        for token in ["platform", "\u5e73\u53f0", "\u5e73\u81fa", "\u5404\u5e73\u53f0", "\u65b0\u4e8b\u696d\u7fa4", "\u4e8b\u696d\u7fa4", "\u4e94\u5927\u7522\u54c1\u7dda", "\u7522\u54c1\u7dda"]
    )
    has_latest = any(
        token in lowered or token in text
        for token in ["latest month", "current month", "this month", "\u6700\u65b0\u6708\u4efd", "\u6700\u65b0\u6708", "\u672c\u6708"]
    )
    has_summary = any(
        token in lowered or token in text
        for token in ["summary", "summarize", "overview", "\u6574\u7406", "\u6458\u8981", "\u91cd\u9ede", "\u72c0\u6cc1"]
    )
    has_revenue_inventory = _contains_any(text, lowered, REVENUE_KEYWORDS) and _contains_any(text, lowered, INVENTORY_KEYWORDS)
    has_operation = any(token in lowered or token in text for token in ["operation", "operational", "\u71df\u904b"])
    return has_platform and has_latest and has_summary and (has_revenue_inventory or has_operation)


def _is_parent_child_drilldown_question(text: str) -> bool:
    return any(token in text for token in ["底下", "下面"]) and any(token in text for token in ["產品線", "五大產品線"])


def _is_contribution_question(text: str, lowered: str) -> bool:
    return any(token in lowered or token in text for token in ["contribution", "contributed", "contribute", "貢獻", "主要來自", "帶動", "造成"])


def _is_entity_time_series_question(text: str, lowered: str) -> bool:
    return any(token in lowered or token in text for token in ["各月", "每月", "近"]) and any(token in lowered or token in text for token in REVENUE_KEYWORDS + INVENTORY_KEYWORDS)


def _is_overall_trend_question(text: str, lowered: str, object_dimension: str | None) -> bool:
    return (object_dimension == "overall" or _contains_any(text, lowered, OVERALL_KEYWORDS)) and _contains_any(text, lowered, TREND_KEYWORDS)


def _is_entity_trend_comparison_question(text: str, lowered: str, object_dimension: str | None) -> bool:
    return object_dimension in {"business_group", "product_line_5"} and _contains_any(text, lowered, TREND_KEYWORDS) and any(
        token in text for token in ["各新事業群", "各事業群", "各產品線", "各五大產品線", "近"]
    )


def _is_single_month_all_entity_table_question(text: str, lowered: str, object_dimension: str | None) -> bool:
    if object_dimension not in {"business_group", "product_line_5"}:
        return False
    if not _extract_single_month(text):
        return False
    has_all_entity = any(token in text for token in ["各事業群", "各新事業群", "各BU", "各 BU", "各產品線", "各五大產品線"])
    has_trigger = _contains_any(text, lowered, LOOKUP_KEYWORDS + COMPARISON_KEYWORDS)
    has_metric_or_data = _contains_any(text, lowered, REVENUE_KEYWORDS + INVENTORY_KEYWORDS) or any(token in text for token in ["資料", "數據"])
    return has_all_entity and has_trigger and has_metric_or_data


def _extract_single_month(text: str) -> str | None:
    match = re.search(r"(20\d{2})\s*[-/\u5e74]?\s*(1[0-2]|0?[1-9])\s*(?:\u6708)?", text)
    return f"{match.group(1)}-{int(match.group(2)):02d}" if match else None


def _default_table_lenses(text: str, lowered: str) -> list[KpiLens]:
    lenses: list[KpiLens] = []
    if _contains_any(text, lowered, REVENUE_KEYWORDS):
        lenses.append(KPI_LENSES["revenue_scale"])
    if _contains_any(text, lowered, INVENTORY_KEYWORDS):
        lenses.append(KPI_LENSES["inventory_efficiency"])
    return lenses or [KPI_LENSES["revenue_scale"]]


def _extract_period_pair(text: str) -> tuple[str, str] | None:
    month_matches = [
        {
            "month": f"{match.group(1)}-{int(match.group(2)):02d}",
            "span": match.span(),
        }
        for match in re.finditer(r"(20\d{2})\s*[-/\u5e74]?\s*(1[0-2]|0?[1-9])\s*(?:\u6708)?", text)
    ]
    months = [item["month"] for item in month_matches]
    if len(months) < 2:
        for match in re.finditer(r"(?<!\d)(1[0-2]|0?[1-9])\s*\u6708", text):
            months.append(f"2024-{int(match.group(1)):02d}")
    unique_months = list(dict.fromkeys(months))
    if len(unique_months) < 2:
        return None
    pair_tokens = [
        "compare",
        "difference",
        "versus",
        " vs ",
        "\u6bd4\u8f03",
        "\u4ee5\u53ca",
        "\u8207",
        "\u548c",
        "\u8ddf",
        "\u5340\u5225",
        "\u5dee\u7570",
        "\u5dee\u591a\u5c11",
    ]
    if any(token in text or token in text.lower() for token in pair_tokens):
        if len(month_matches) >= 2:
            first = month_matches[0]
            second = month_matches[1]
            connector = text[first["span"][1] : second["span"][0]]
            if "比" in connector and not any(token in connector for token in ["與", "和", "以及", "跟"]):
                return second["month"], first["month"]
        return unique_months[0], unique_months[1]
    return None


def _is_comparison(text: str, lowered: str) -> bool:
    if len(re.findall(r"GG-(0[1-9]|[1-8][0-9]|9[0-1])", text.upper())) >= 2:
        return True
    return _contains_any(text, lowered, COMPARISON_KEYWORDS)


def _is_proxy_anomaly_question(text: str, lowered: str) -> bool:
    has_revenue = _contains_any(text, lowered, REVENUE_KEYWORDS)
    has_inventory = _contains_any(text, lowered, INVENTORY_KEYWORDS)
    has_down = any(token in lowered for token in ["down", "decline", "下降"])
    has_up = any(token in lowered for token in ["up", "rise", "增加", "上升"])
    has_divergence = any(token in lowered for token in ["背離", "divergence", "異常", "anomaly"])
    return has_revenue and has_inventory and ((has_down and has_up) or has_divergence)


def _is_performance_weakness_question(text: str, lowered: str, object_dimension: str | None) -> bool:
    has_platform_context = (
        object_dimension in {"platform", "business_group", "product_line_5"}
        or _contains_any(text, lowered, PLATFORM_KEYWORDS + GROUP_KEYWORDS + PRODUCT_LINE_KEYWORDS)
        or "平台" in text
    )
    if not has_platform_context:
        return False

    has_weakness_phrase = any(keyword.lower() in lowered for keyword in PERFORMANCE_WEAKNESS_KEYWORDS)
    has_efficiency_context = _contains_any(text, lowered, EFFICIENCY_KEYWORDS) or (
        _contains_any(text, lowered, REVENUE_KEYWORDS) and _contains_any(text, lowered, INVENTORY_KEYWORDS)
    )
    has_attention_context = any(token in text for token in ["需要注意", "有問題", "狀況不好", "效率差", "表現"]) or any(
        token in lowered for token in ["attention", "problem", "poorly", "weaker"]
    )
    return has_weakness_phrase and (has_efficiency_context or has_attention_context or has_platform_context)


def _detect_object_dimension(text: str, lowered: str) -> str | None:
    if _contains_any(text, lowered, OVERALL_KEYWORDS):
        return "overall"
    if _contains_any(text, lowered, PRODUCT_LINE_KEYWORDS):
        return "product_line_5"
    if _contains_any(text, lowered, GROUP_KEYWORDS):
        return "business_group"
    if any(token in text for token in ["平台", "平臺"]):
        return "business_group"
    if _contains_any(text, lowered, PLATFORM_KEYWORDS):
        return "business_group"
    if _contains_any(text, lowered, MONTH_KEYWORDS):
        return "month"
    return None


def _detect_kpi_lenses(text: str, lowered: str) -> list[KpiLens]:
    lenses: list[KpiLens] = []

    has_revenue = _contains_any(text, lowered, REVENUE_KEYWORDS)
    has_inventory = _contains_any(text, lowered, INVENTORY_KEYWORDS)
    has_efficiency = _contains_any(text, lowered, EFFICIENCY_KEYWORDS)
    has_risk = _contains_any(text, lowered, RISK_KEYWORDS)
    has_trend = _contains_any(text, lowered, TREND_KEYWORDS)

    if has_revenue:
        lenses.append(KPI_LENSES["revenue_scale"])
    if has_revenue and has_trend:
        lenses.append(KPI_LENSES["revenue_growth"])
    if has_inventory or has_efficiency:
        lenses.append(KPI_LENSES["inventory_efficiency"])
    if has_risk:
        lenses.append(KPI_LENSES["risk_anomaly"])
    if not lenses and any(token in lowered for token in ["priority", "performance", "health", "表現", "體質"]):
        lenses.append(KPI_LENSES["overall_health"])

    seen: set[str] = set()
    unique_lenses: list[KpiLens] = []
    for lens in lenses:
        if lens.name not in seen:
            unique_lenses.append(lens)
            seen.add(lens.name)
    return unique_lenses


def _ranking_domains(text: str, lowered: str) -> list[str]:
    if _contains_any(text, lowered, INVENTORY_KEYWORDS) and not _contains_any(text, lowered, REVENUE_KEYWORDS):
        return ["inventory"]
    if _contains_any(text, lowered, EFFICIENCY_KEYWORDS):
        return ["financial"]
    return ["sales"]


def _trend_domains(text: str, lowered: str) -> list[str]:
    has_revenue = _contains_any(text, lowered, REVENUE_KEYWORDS)
    has_inventory = _contains_any(text, lowered, INVENTORY_KEYWORDS)
    if has_revenue and has_inventory:
        return ["sales", "inventory", "financial"]
    if has_inventory and not has_revenue:
        return ["inventory"]
    return ["sales"]


def _diagnosis_domains(text: str, lowered: str) -> list[str]:
    has_revenue = _contains_any(text, lowered, REVENUE_KEYWORDS)
    has_inventory = _contains_any(text, lowered, INVENTORY_KEYWORDS)
    if has_revenue and has_inventory:
        return ["sales", "inventory", "financial"]
    if has_inventory and not has_revenue:
        return ["inventory", "financial"]
    if has_revenue:
        return ["sales", "financial"]
    return ["financial"]


def _default_ranking_lenses(text: str, lowered: str) -> list[KpiLens]:
    if _contains_any(text, lowered, INVENTORY_KEYWORDS) and not _contains_any(text, lowered, REVENUE_KEYWORDS):
        return [KPI_LENSES["inventory_efficiency"]]
    return [KPI_LENSES["revenue_scale"]]


def _default_trend_lenses(text: str, lowered: str) -> list[KpiLens]:
    if _contains_any(text, lowered, INVENTORY_KEYWORDS) and not _contains_any(text, lowered, REVENUE_KEYWORDS):
        return [KPI_LENSES["inventory_efficiency"]]
    return [KPI_LENSES["revenue_growth"]]


def _domains_for_lenses(lenses: list[KpiLens]) -> list[str]:
    domains: list[str] = []
    lens_names = {lens.name for lens in lenses}
    if "revenue_scale" in lens_names or "revenue_growth" in lens_names:
        domains.append("sales")
    if "inventory_efficiency" in lens_names:
        domains.append("inventory")
    if "risk_anomaly" in lens_names or "overall_health" in lens_names:
        domains.append("financial")
    return domains
