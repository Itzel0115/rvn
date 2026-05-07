from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import QA_TRANSCRIPT_FILE
from llm_reporter import generate_qa_llm_answer
from utils import MessageCollector, format_number


def start_chat_loop(artifacts, parsed_mapping) -> MessageCollector:
    collector = MessageCollector()
    transcript_lines = ["# QA Transcript", ""]
    print("已進入問答模式。輸入問題後按 Enter，輸入 exit 離開。")

    while True:
        try:
            question = input("問題> ").strip()
        except EOFError:
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            break

        answer, qa_messages = answer_question(question, artifacts, parsed_mapping)
        collector.extend(qa_messages)
        transcript_lines.extend([f"## 問題", "", question, "", "## 回答", "", answer, ""])
        print(answer)
        print("")

    QA_TRANSCRIPT_FILE.write_text("\n".join(transcript_lines), encoding="utf-8")
    return collector


def answer_question(question: str, artifacts, parsed_mapping) -> tuple[str, MessageCollector]:
    collector = MessageCollector()
    retrieved_sections = retrieve_relevant_data(question, artifacts, parsed_mapping)
    programmatic_summary = build_programmatic_summary(question, artifacts, parsed_mapping)
    context = {
        "question": question,
        "retrieved_records_markdown": retrieved_sections,
        "programmatic_summary": programmatic_summary,
        "report_context": artifacts.report_context,
    }
    ai_answer, llm_messages = generate_qa_llm_answer(question, context)
    collector.extend(llm_messages)
    final_answer = "\n\n".join(
        [
            "## 查找的資料",
            retrieved_sections,
            "## 程式分析結果",
            programmatic_summary,
            "## AI分析結果",
            ai_answer,
        ]
    )
    return final_answer, collector


def retrieve_relevant_data(question: str, artifacts, parsed_mapping) -> str:
    month_match = _extract_month(question)
    platform_match = _extract_platform(question)
    group_match = _extract_group(question, parsed_mapping.business_group_mapping)
    intent = detect_question_intent(question)

    dynamic_tables = build_dynamic_tables(question, artifacts, month_match, platform_match, group_match)
    selected_tables: list[tuple[str, pd.DataFrame]] = list(dynamic_tables)

    if not selected_tables:
        selected_tables.extend(select_static_tables(intent, artifacts, group_match, platform_match))

    if not selected_tables:
        selected_tables = [
            ("monthly_revenue", artifacts.monthly_revenue),
            ("monthly_inventory_amount", artifacts.monthly_inventory_amount),
            ("anomalies", artifacts.anomalies),
            ("correlation_analysis", artifacts.correlation_analysis),
        ]

    lines = []
    for table_name, df in selected_tables:
        filtered = _filter_dataframe(df, month_match, platform_match, group_match)
        if filtered.empty:
            continue
        lines.append(f"### {table_name}")
        for _, row in filtered.head(8).iterrows():
            parts = [f"{col}={_stringify_value(row.get(col))}" for col in filtered.columns[: min(6, len(filtered.columns))]]
            lines.append(f"- {' / '.join(parts)}")
        lines.append("")

    if not lines:
        return "- 沒有找到完全符合條件的片段，請改問月份、平台代碼、事業群或異常類型。"
    return "\n".join(lines).strip()


def build_programmatic_summary(question: str, artifacts, parsed_mapping) -> str:
    lines: list[str] = []
    lowered = question.lower()
    month_match = _extract_month(question)
    platform_match = _extract_platform(question)
    group_match = _extract_group(question, parsed_mapping.business_group_mapping)
    intent = detect_question_intent(question)

    dynamic_tables = build_dynamic_tables(question, artifacts, month_match, platform_match, group_match)
    for table_name, df in dynamic_tables:
        if df.empty:
            continue
        if table_name in {"group_monthly_revenue", "platform_monthly_revenue", "group_monthly_inventory_amount", "group_monthly_inventory_qty", "platform_monthly_inventory"}:
            value_column = _first_existing_column(df, ["營收", "金額", "QTY"])
            if value_column:
                lines.extend(_summarize_recent_points(df, value_column))

    if any(word in lowered for word in ["關聯", "相關"]):
        if artifacts.correlation_analysis.empty:
            lines.append("- 目前沒有足夠資料點可做關聯性分析。")
        else:
            top = artifacts.correlation_analysis.sort_values("樣本數", ascending=False).head(5)
            for _, row in top.iterrows():
                corr = row.get("相關係數")
                corr_text = "N/A" if pd.isna(corr) else f"{corr:.3f}"
                lines.append(
                    f"- {row.get('指標組合')}: 相關係數 {corr_text}，判讀為 {row.get('關聯判讀')}，樣本數 {row.get('樣本數')}"
                )

    if intent["anomaly"]:
        if artifacts.anomalies.empty:
            lines.append("- 目前沒有超過門檻的異常。")
        else:
            for _, row in artifacts.anomalies.head(5).iterrows():
                lines.append(
                    f"- {row.get('月份')} / {row.get('異常類型')} / 群組 {row.get('新事業群', 'N/A')} / 平台 {row.get('平台', 'N/A')}"
                )

    has_specific_scope = bool(group_match or platform_match or month_match)

    if intent["revenue"] and intent["trend"] and not has_specific_scope:
        lines.extend(_summarize_recent_points(artifacts.monthly_revenue, "營收"))

    if intent["inventory"] and intent["trend"] and not has_specific_scope:
        lines.extend(_summarize_recent_points(artifacts.monthly_inventory_amount, "金額"))
        lines.extend(_summarize_recent_points(artifacts.monthly_inventory_qty, "QTY"))

    if intent["platform"] and intent["ratio"] and not artifacts.platform_monthly_analysis.empty:
        latest = artifacts.platform_monthly_analysis.sort_values("月份").tail(5)
        for _, row in latest.iterrows():
            lines.append(
                f"- 平台 {row.get('平台')} / {row.get('月份')} / 營收 {format_number(row.get('營收'))} / "
                f"庫存金額 {format_number(row.get('金額'))} / 營收庫存金額比 {format_number(row.get('營收_庫存金額比'))}"
            )

    if not lines:
        lines.append("- 可回答的方向包含月份趨勢、事業群分布、平台比值、異常與關聯性分析。")
        if parsed_mapping.mapping_success:
            lines.append("- 目前系統有建立部分 HQBU -> 平台整合，可支援部分平台層級問答。")
        else:
            lines.append("- 目前系統未完整建立 HQBU -> 平台整合，平台相關問答可能只反映營收端資料。")

    return "\n".join(lines)


def _filter_dataframe(
    df: pd.DataFrame,
    month_match: str | None,
    platform_match: str | None,
    group_match: str | None,
) -> pd.DataFrame:
    if df.empty:
        return df

    filtered = df.copy()
    if month_match and "月份" in filtered.columns:
        filtered = filtered.loc[filtered["月份"].astype(str) == month_match]
    if platform_match and "平台" in filtered.columns:
        filtered = filtered.loc[filtered["平台"].astype(str).str.upper() == platform_match]
    if group_match:
        if "新事業群" in filtered.columns:
            filtered = filtered.loc[filtered["新事業群"].astype(str) == group_match]
        elif "分析對象" in filtered.columns:
            filtered = filtered.loc[filtered["分析對象"].astype(str) == group_match]
    return filtered


def _extract_month(question: str) -> str | None:
    month = re.search(r"(20\d{2})[-/]?(0[1-9]|1[0-2])", question)
    if not month:
        return None
    return f"{month.group(1)}-{month.group(2)}"


def _extract_platform(question: str) -> str | None:
    match = re.search(r"GG-(0[1-9]|[1-8][0-9]|9[0-1])", question.upper())
    return match.group(0) if match else None


def _extract_group(question: str, business_groups: pd.DataFrame) -> str | None:
    normalized = question.replace("　", " ")
    direct = re.search(r"事業群\s*[:：]?\s*([0-9]+)", normalized)
    if direct:
        return direct.group(1)
    fallback = re.search(r"\b([0-9]+)\b", normalized)
    if "事業群" in normalized and fallback:
        return fallback.group(1)
    if business_groups.empty:
        return None
    for _, row in business_groups.iterrows():
        name = str(row.get("事業群名稱", ""))
        if name and name in question:
            return str(row.get("事業群代碼"))
    return None


def _summarize_recent_points(df: pd.DataFrame, value_column: str) -> list[str]:
    if df.empty:
        return [f"- {value_column} 沒有可用資料。"]
    lines = []
    sort_col = "月份" if "月份" in df.columns else df.columns[0]
    recent = df.sort_values(sort_col).tail(3)
    for _, row in recent.iterrows():
        mom = row.get("月增率")
        mom_text = "N/A" if pd.isna(mom) else f"{mom:.2%}"
        month_text = row.get("月份", "N/A")
        lines.append(f"- {month_text} 的 {value_column} 為 {format_number(row.get(value_column))}，月增率 {mom_text}")
    return lines


def _stringify_value(value) -> str:
    if isinstance(value, float):
        return format_number(value)
    if pd.isna(value):
        return "N/A"
    return str(value)


def build_dynamic_tables(
    question: str,
    artifacts,
    month_match: str | None,
    platform_match: str | None,
    group_match: str | None,
) -> list[tuple[str, pd.DataFrame]]:
    lowered = question.lower()
    tables: list[tuple[str, pd.DataFrame]] = []
    intent = detect_question_intent(question)

    if intent["revenue"] and group_match:
        df = (
            artifacts.revenue_enriched.loc[
                artifacts.revenue_enriched["新事業群"].astype(str) == str(group_match)
            ]
            .groupby("月份", as_index=False)["營收"]
            .sum(min_count=1)
            .sort_values("月份")
            .reset_index(drop=True)
        )
        if not df.empty:
            df["月增率"] = df["營收"].pct_change()
            tables.append(("group_monthly_revenue", _filter_dataframe(df, month_match, platform_match, group_match)))

    if intent["inventory"] and intent["amount"] and group_match:
        df = (
            artifacts.inventory_enriched.loc[
                artifacts.inventory_enriched["新事業群"].astype(str) == str(group_match)
            ]
            .groupby("月份", as_index=False)["金額"]
            .sum(min_count=1)
            .sort_values("月份")
            .reset_index(drop=True)
        )
        if not df.empty:
            df["月增率"] = df["金額"].pct_change()
            tables.append(("group_monthly_inventory_amount", _filter_dataframe(df, month_match, platform_match, group_match)))

    if intent["inventory"] and intent["qty"] and group_match:
        df = (
            artifacts.inventory_enriched.loc[
                artifacts.inventory_enriched["新事業群"].astype(str) == str(group_match)
            ]
            .groupby("月份", as_index=False)["QTY"]
            .sum(min_count=1)
            .sort_values("月份")
            .reset_index(drop=True)
        )
        if not df.empty:
            df["月增率"] = df["QTY"].pct_change()
            tables.append(("group_monthly_inventory_qty", _filter_dataframe(df, month_match, platform_match, group_match)))

    if intent["revenue"] and platform_match:
        df = (
            artifacts.revenue_enriched.loc[
                artifacts.revenue_enriched["平台"].astype(str).str.upper() == platform_match
            ]
            .groupby("月份", as_index=False)["營收"]
            .sum(min_count=1)
            .sort_values("月份")
            .reset_index(drop=True)
        )
        if not df.empty:
            df["月增率"] = df["營收"].pct_change()
            tables.append(("platform_monthly_revenue", _filter_dataframe(df, month_match, platform_match, group_match)))

    if intent["inventory"] and platform_match:
        inventory = artifacts.inventory_enriched
        if "平台" in inventory.columns:
            df = (
                inventory.loc[inventory["平台"].astype(str).str.upper() == platform_match]
                .groupby("月份", as_index=False)[["金額", "QTY"]]
                .sum(min_count=1)
                .sort_values("月份")
                .reset_index(drop=True)
            )
            if not df.empty:
                df["金額月增率"] = df["金額"].pct_change()
                df["QTY月增率"] = df["QTY"].pct_change()
                tables.append(("platform_monthly_inventory", _filter_dataframe(df, month_match, platform_match, group_match)))

    return tables


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def detect_question_intent(question: str) -> dict[str, bool]:
    lowered = question.lower()
    return {
        "revenue": "營收" in question,
        "inventory": "庫存" in question,
        "amount": "金額" in question,
        "qty": "qty" in lowered or "數量" in question,
        "trend": any(token in question for token in ["走勢", "趨勢", "變化", "每月", "月份"]),
        "distribution": any(token in question for token in ["分布", "占比", "結構"]),
        "anomaly": any(token in question for token in ["異常", "風險", "異動"]),
        "correlation": any(token in question for token in ["關聯", "相關", "相關性", "correlation"]),
        "ratio": "比值" in question or "比率" in question,
        "platform": "平台" in question,
        "group": "事業群" in question,
    }


def select_static_tables(intent: dict[str, bool], artifacts, group_match: str | None, platform_match: str | None) -> list[tuple[str, pd.DataFrame]]:
    tables: list[tuple[str, pd.DataFrame]] = []

    if intent["correlation"]:
        tables.append(("correlation_analysis", artifacts.correlation_analysis))
    if intent["anomaly"]:
        tables.append(("anomalies", artifacts.anomalies))
    if intent["platform"] and intent["ratio"]:
        tables.append(("platform_monthly_analysis", artifacts.platform_monthly_analysis))

    if not (group_match or platform_match):
        if intent["revenue"] and intent["trend"]:
            tables.append(("monthly_revenue", artifacts.monthly_revenue))
        if intent["inventory"] and intent["trend"] and intent["amount"]:
            tables.append(("monthly_inventory_amount", artifacts.monthly_inventory_amount))
        if intent["inventory"] and intent["trend"] and intent["qty"]:
            tables.append(("monthly_inventory_qty", artifacts.monthly_inventory_qty))
        if intent["group"] and intent["revenue"] and intent["distribution"]:
            tables.append(("revenue_by_group", artifacts.revenue_by_group))
        if intent["group"] and intent["inventory"] and intent["distribution"]:
            tables.append(("inventory_by_group", artifacts.inventory_by_group))

    return tables
