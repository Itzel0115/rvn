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
CHART_KEYWORDS = ["chart", "plot", "graph", "visual", "圖", "畫圖", "圖表", "視覺化", "趨勢圖"]
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
]

REVENUE_KEYWORDS = ["revenue", "sales", "sell", "營收", "銷售"]
INVENTORY_KEYWORDS = ["inventory", "stock", "qty", "庫存", "存貨", "金額", "數量"]
EFFICIENCY_KEYWORDS = ["ratio", "efficiency", "營收/庫存", "庫存/營收", "效率", "週轉", "周轉", "proxy"]
PLATFORM_KEYWORDS = ["platform", "平台", "平臺", "gg-"]
GROUP_KEYWORDS = ["group", "business group", "新事業群", "事業群", "群組"]
MONTH_KEYWORDS = ["month", "months", "月份", "本月", "最新月份", "最新月", "latest month", "current month"]


def classify_business_question(question: str) -> BusinessQuestionProfile:
    text = question.strip()
    lowered = text.lower()

    object_dimension = _detect_object_dimension(text, lowered)
    needs_chart = _contains_any(text, lowered, CHART_KEYWORDS)
    kpi_lenses = _detect_kpi_lenses(text, lowered)

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

    if _is_proxy_anomaly_question(text, lowered):
        return BusinessQuestionProfile(
            question_type="diagnosis",
            intents=["diagnosis", "risk", "anomaly"],
            domains=["sales", "inventory", "financial"],
            kpi_lenses=[KPI_LENSES["overall_health"], KPI_LENSES["risk_anomaly"]],
            object_dimension=object_dimension,
            answer_strategy="diagnosis",
            needs_chart=needs_chart,
            warnings=["這類問題目前只能用營收與庫存的代理異常訊號回答，不能直接判定根本原因。"],
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
            object_dimension="platform" if object_dimension == "platform" else object_dimension,
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
        return BusinessQuestionProfile(
            question_type="query",
            intents=["metric_query"],
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
    has_platform_context = object_dimension == "platform" or _contains_any(text, lowered, PLATFORM_KEYWORDS) or "平台" in text
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
    if any(token in text for token in ["平台", "平臺"]):
        return "platform"
    if _contains_any(text, lowered, PLATFORM_KEYWORDS):
        return "platform"
    if _contains_any(text, lowered, GROUP_KEYWORDS):
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
