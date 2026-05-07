from __future__ import annotations

import argparse
import json
import pandas as pd

from analysis_pipeline import build_pipeline_context
from analyzer import analyze_data
from config import (
    ANALYSIS_REPORT_FILE,
    CHART_DIR,
    CLEANED_INVENTORY_FILE,
    CLEANED_REVENUE_FILE,
    DATA_DIR,
    INVENTORY_FILE,
    LLM_EXPLANATION_FILE,
    MAPPING_FILE,
    MERGED_ANALYSIS_FILE,
    OUTPUT_DIR,
    PARSED_MAPPING_FILE,
    QA_TRANSCRIPT_FILE,
    REVENUE_FILE,
    SUMMARY_METRICS_FILE,
)
from data_loader import load_inventory, load_mapping_raw, load_revenue
from llm_reporter import generate_llm_explanation
from logging_utils import configure_logging, get_logger
from mapping_parser import parse_mapping
from multi_agent import MultiAgentAssistant
from qa_engine import start_chat_loop
from test_data_generator import generate_test_data
from utils import MessageCollector, ensure_directories, format_number
from visualizer import create_all_charts


def main() -> None:
    args = parse_args()
    ensure_directories([DATA_DIR, OUTPUT_DIR, CHART_DIR])

    agent_question = args.agent_question or args.question
    agent_project_summary = args.agent_project_summary or args.project_summary

    if agent_question or agent_project_summary:
        args.agent_question = agent_question
        args.agent_project_summary = agent_project_summary
        run_multi_agent_mode(args)
        return

    if args.generate_test_data:
        test_messages = generate_test_data()
        for info in test_messages.infos:
            print(info)

    all_messages = MessageCollector()

    inventory_df, inventory_check, inventory_messages = load_inventory(INVENTORY_FILE)
    revenue_df, revenue_check, revenue_messages = load_revenue(REVENUE_FILE)
    mapping_raw_df, mapping_messages = load_mapping_raw(MAPPING_FILE)

    all_messages.extend(inventory_messages)
    all_messages.extend(revenue_messages)
    all_messages.extend(mapping_messages)

    parsed_mapping, mapping_parse_messages = parse_mapping(mapping_raw_df)
    all_messages.extend(mapping_parse_messages)

    if inventory_check.get("missing") or revenue_check.get("missing") or parsed_mapping.structured_mapping.empty:
        write_failure_report(inventory_check, revenue_check, parsed_mapping, all_messages)
        print("必要資料或欄位不足，已輸出失敗報告至 output/analysis_report.md")
        return

    artifacts, analysis_messages = analyze_data(inventory_df, revenue_df, parsed_mapping)
    all_messages.extend(analysis_messages)

    export_outputs(inventory_df, revenue_df, parsed_mapping, artifacts)

    chart_messages = create_all_charts(artifacts, CHART_DIR)
    all_messages.extend(chart_messages)

    write_analysis_report(inventory_check, revenue_check, parsed_mapping, artifacts, all_messages)

    llm_messages = generate_llm_explanation(artifacts.report_context, LLM_EXPLANATION_FILE)
    all_messages.extend(llm_messages)

    if args.chat:
        qa_messages = start_chat_loop(artifacts, parsed_mapping)
        all_messages.extend(qa_messages)
        print(f"問答紀錄已輸出至 {QA_TRANSCRIPT_FILE}")

    print("分析完成，輸出檔案位於 output/ 目錄。")
    if all_messages.warnings:
        print(f"警告數量: {len(all_messages.warnings)}，請查看 {ANALYSIS_REPORT_FILE}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="去識別化營收與庫存分析工具")
    parser.add_argument("--chat", action="store_true", help="分析完成後進入終端問答模式")
    parser.add_argument("--generate-test-data", action="store_true", help="依規格重建 data/ 內的測試 Excel")
    parser.add_argument("--agent-question", type=str, help="使用多 Agent assistant 回答單一問題")
    parser.add_argument("--question", type=str, help="`--agent-question` 的相容別名")
    parser.add_argument("--agent-project-summary", action="store_true", help="輸出目前專案與資料摘要")
    parser.add_argument("--project-summary", action="store_true", help="`--agent-project-summary` 的相容別名")
    parser.add_argument("--agent-json", action="store_true", help="以 JSON 格式輸出 multi-agent 結果")
    parser.add_argument("--agent-debug", action="store_true", help="開啟 multi-agent debug logging")
    return parser.parse_args()


def run_multi_agent_mode(args: argparse.Namespace) -> None:
    request_id = configure_logging(OUTPUT_DIR / "logs", debug=args.agent_debug)
    logger = get_logger("main", request_id, domain="system")
    logger.info("Starting multi-agent mode from main.py")

    context = build_pipeline_context(request_id)
    assistant = MultiAgentAssistant(context, request_id)

    if args.agent_project_summary:
        summary = assistant.summarize_project()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not args.agent_question:
            return

    question = args.agent_question or input("請輸入問題: ").strip()
    if not question:
        raise SystemExit("問題不可為空。")

    response = assistant.answer(question)
    if args.agent_json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
    else:
        print(response["summary"])


def export_outputs(inventory_df, revenue_df, parsed_mapping, artifacts) -> None:
    inventory_df.to_excel(CLEANED_INVENTORY_FILE, index=False)
    revenue_df.to_excel(CLEANED_REVENUE_FILE, index=False)

    with pd.ExcelWriter(PARSED_MAPPING_FILE, engine="openpyxl") as writer:
        parsed_mapping.structured_mapping.to_excel(writer, sheet_name="structured_mapping", index=False)
        parsed_mapping.business_group_mapping.to_excel(writer, sheet_name="business_groups", index=False)
        parsed_mapping.inventory_hqbu_mapping.to_excel(writer, sheet_name="inventory_hqbu", index=False)
        parsed_mapping.revenue_platform_mapping.to_excel(writer, sheet_name="revenue_platform", index=False)
        parsed_mapping.anonymization_rules.to_excel(writer, sheet_name="anonymization_rules", index=False)
        parsed_mapping.bridge_candidates.to_excel(writer, sheet_name="bridge_candidates", index=False)

    with pd.ExcelWriter(MERGED_ANALYSIS_FILE, engine="openpyxl") as writer:
        artifacts.inventory_enriched.to_excel(writer, sheet_name="inventory_enriched", index=False)
        artifacts.revenue_enriched.to_excel(writer, sheet_name="revenue_enriched", index=False)
        artifacts.merged_analysis.to_excel(writer, sheet_name="merged_analysis", index=False)
        artifacts.platform_monthly_analysis.to_excel(writer, sheet_name="platform_monthly", index=False)
        artifacts.anomalies.to_excel(writer, sheet_name="anomalies", index=False)
        artifacts.correlation_analysis.to_excel(writer, sheet_name="correlations", index=False)

    with pd.ExcelWriter(SUMMARY_METRICS_FILE, engine="openpyxl") as writer:
        for sheet_name, df in artifacts.summary_metrics.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)


def write_failure_report(inventory_check, revenue_check, parsed_mapping, messages: MessageCollector) -> None:
    lines = [
        "# 分析報告",
        "",
        "## 執行狀態",
        "",
        "- 狀態: 失敗",
        "- 原因: 必要欄位缺漏或 mapping 結構不足，無法進入正式分析流程。",
        "",
        "## 欄位檢查結果",
        "",
        f"- 庫存缺少欄位: {inventory_check.get('missing', [])}",
        f"- 營收缺少欄位: {revenue_check.get('missing', [])}",
        f"- mapping 結構化列數: {len(parsed_mapping.structured_mapping)}",
        "",
        "## 錯誤與警告",
        "",
    ]
    for message in messages.errors:
        lines.append(f"- 錯誤: {message}")
    for message in messages.warnings:
        lines.append(f"- 警告: {message}")
    ANALYSIS_REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")


def write_analysis_report(inventory_check, revenue_check, parsed_mapping, artifacts, messages: MessageCollector) -> None:
    report: list[str] = ["# 分析報告", ""]

    report.extend(["## 1. 資料概況", ""])
    report.extend(
        [
            f"- 庫存資料筆數: {len(artifacts.inventory_enriched)}",
            f"- 營收資料筆數: {len(artifacts.revenue_enriched)}",
            f"- mapping 結構列數: {len(parsed_mapping.structured_mapping)}",
            f"- 月份範圍（庫存）: {artifacts.inventory_enriched['月份'].min()} ~ {artifacts.inventory_enriched['月份'].max()}",
            f"- 月份範圍（營收）: {artifacts.revenue_enriched['月份'].min()} ~ {artifacts.revenue_enriched['月份'].max()}",
            "",
        ]
    )

    report.extend(["## 2. 欄位檢查結果", ""])
    report.extend(
        [
            f"- 庫存必要欄位缺漏: {inventory_check.get('missing', []) or '無'}",
            f"- 營收必要欄位缺漏: {revenue_check.get('missing', []) or '無'}",
            f"- 庫存額外欄位: {inventory_check.get('extra', []) or '無'}",
            f"- 營收額外欄位: {revenue_check.get('extra', []) or '無'}",
            "",
        ]
    )

    report.extend(["## 3. 去識別化-分類解析結果", ""])
    report.extend(
        [
            f"- 新事業群分類數: {parsed_mapping.business_group_mapping['事業群代碼'].nunique() if not parsed_mapping.business_group_mapping.empty else 0}",
            f"- 庫存 HQBU 代碼數: {parsed_mapping.inventory_hqbu_mapping['庫存HQBU代碼'].nunique() if not parsed_mapping.inventory_hqbu_mapping.empty else 0}",
            f"- 營收平台代碼數: {parsed_mapping.revenue_platform_mapping['營收平台代碼'].nunique() if not parsed_mapping.revenue_platform_mapping.empty else 0}",
            f"- HQBU -> 平台候選對應數: {len(parsed_mapping.bridge_candidates)}",
            "",
        ]
    )

    report.extend(["## 4. 新事業群 / HQBU / 平台分類摘要", ""])
    report.extend(dataframe_rows_to_bullets(parsed_mapping.business_group_mapping.head(10), ["事業群代碼", "事業群名稱"]))
    report.extend(
        dataframe_rows_to_bullets(
            parsed_mapping.inventory_hqbu_mapping.head(10),
            ["事業群代碼", "庫存HQBU代碼", "庫存HQBU分類名稱"],
        )
    )
    report.extend(
        dataframe_rows_to_bullets(
            parsed_mapping.revenue_platform_mapping.head(10),
            ["事業群代碼", "營收平台代碼", "營收平台分類名稱"],
        )
    )
    report.append("")

    report.extend(["## 5. 金額 / QTY / 營收處理方式摘要", ""])
    rule_preview = parsed_mapping.anonymization_rules.head(10)
    if rule_preview.empty:
        report.append("- 無可用規則說明資料。")
    else:
        for _, row in rule_preview.iterrows():
            report.append(
                "- "
                f"事業群 {row.get('事業群代碼', 'N/A')} / "
                f"HQBU {row.get('庫存HQBU代碼', 'N/A')} / "
                f"平台 {row.get('營收平台代碼', 'N/A')} / "
                f"金額 {row.get('金額處理方式', 'N/A')} / "
                f"QTY {row.get('QTY處理方式', 'N/A')} / "
                f"營收 {row.get('實際營收處理方式', 'N/A')}"
            )
    report.append("")

    report.extend(["## 6. 趨勢分析結果", ""])
    report.extend(summarize_monthly_table(artifacts.monthly_revenue, "營收", "各月份總營收趨勢"))
    report.extend(summarize_monthly_table(artifacts.monthly_inventory_amount, "金額", "各月份總庫存金額趨勢"))
    report.extend(summarize_monthly_table(artifacts.monthly_inventory_qty, "QTY", "各月份總庫存 QTY 趨勢"))
    report.extend(summarize_group_table(artifacts.revenue_by_group, "營收", "各新事業群營收分布"))
    report.extend(summarize_group_table(artifacts.inventory_by_group, "金額", "各新事業群庫存分布"))

    if not artifacts.platform_monthly_analysis.empty:
        report.extend(["### 平台整合分析", ""])
        for _, row in artifacts.platform_monthly_analysis.head(15).iterrows():
            report.append(
                "- "
                f"{row.get('月份')} / 群組 {row.get('新事業群')} / 平台 {row.get('平台')} / "
                f"營收 {format_number(row.get('營收'))} / "
                f"庫存金額 {format_number(row.get('金額'))} / "
                f"QTY {format_number(row.get('QTY'))} / "
                f"營收/庫存金額比 {format_number(row.get('營收_庫存金額比'))} / "
                f"營收/庫存QTY比 {format_number(row.get('營收_庫存QTY比'))}"
            )
        report.append("")

    report.extend(["## 7. 異常偵測結果", ""])
    if artifacts.anomalies.empty:
        report.append("- 未偵測到超過門檻的異常訊號。")
    else:
        for _, row in artifacts.anomalies.head(30).iterrows():
            report.append(
                "- "
                f"{row.get('月份', 'N/A')} / 類型 {row.get('異常類型', 'N/A')} / "
                f"群組 {row.get('新事業群', 'N/A')} / 平台 {row.get('平台', 'N/A')} / "
                f"說明: {row.get('說明', 'N/A')}"
            )
    report.append("")

    report.extend(["## 8. 關聯性分析結果", ""])
    if artifacts.correlation_analysis.empty:
        report.append("- 目前沒有足夠資料點可完成關聯性分析。")
    else:
        for _, row in artifacts.correlation_analysis.iterrows():
            corr = row.get("相關係數")
            corr_text = "N/A" if pd.isna(corr) else f"{corr:.3f}"
            report.append(
                f"- {row.get('指標組合')} / 樣本數 {row.get('樣本數')} / 相關係數 {corr_text} / 判讀 {row.get('關聯判讀')}"
            )
    report.append("")

    report.extend(["## 9. 是否成功建立 HQBU → 平台整合", ""])
    if parsed_mapping.mapping_success and not artifacts.platform_monthly_analysis.empty:
        report.append("- 已建立部分 HQBU → 平台整合，可在可解析範圍內進行平台層級比較。")
    else:
        report.append("- 未能可靠完成 HQBU → 平台整合，因此庫存與營收仍需部分分開解讀。")
    report.append("")

    report.extend(["## 10. 分析限制與風險說明", ""])
    report.extend(
        [
            "- 數值已去識別化，不應將分析結果直接視為原始真實商業規模。",
            "- mapping 中的 E/F/I 欄位屬於處理方式說明 metadata，不可用於還原原始數值。",
            "- 本分析較適合觀察趨勢、相對變化、群組差異與異常訊號，不宜過度解讀絕對值。",
            "- HQBU 與平台雖使用相近代碼體系，但未必逐筆一對一，跨表整合需以 mapping 可支持的範圍為準。",
            "",
        ]
    )

    if messages.errors or messages.warnings or messages.infos:
        report.extend(["## 附錄：執行訊息", ""])
        for msg in messages.errors:
            report.append(f"- 錯誤: {msg}")
        for msg in messages.warnings:
            report.append(f"- 警告: {msg}")
        for msg in messages.infos:
            report.append(f"- 資訊: {msg}")

    ANALYSIS_REPORT_FILE.write_text("\n".join(report), encoding="utf-8")


def dataframe_rows_to_bullets(df: pd.DataFrame, columns: list[str]) -> list[str]:
    if df.empty:
        return ["- 無資料。"]

    rows: list[str] = []
    for _, row in df.iterrows():
        parts = [f"{column}: {row.get(column, 'N/A')}" for column in columns]
        rows.append(f"- {' / '.join(parts)}")
    return rows


def summarize_monthly_table(df: pd.DataFrame, value_column: str, title: str) -> list[str]:
    lines = [f"### {title}", ""]
    if df.empty:
        lines.extend(["- 無資料。", ""])
        return lines

    for _, row in df.iterrows():
        mom_value = row.get("月增率")
        mom_text = "N/A" if pd.isna(mom_value) else f"{mom_value:.2%}"
        lines.append(
            f"- {row.get('月份')} / {value_column}: {format_number(row.get(value_column))} / 月增率: {mom_text}"
        )
    lines.append("")
    return lines


def summarize_group_table(df: pd.DataFrame, value_column: str, title: str) -> list[str]:
    lines = [f"### {title}", ""]
    if df.empty:
        lines.extend(["- 無資料。", ""])
        return lines

    for _, row in df.iterrows():
        share_value = row.get("占比")
        share_text = "N/A" if pd.isna(share_value) else f"{share_value:.2%}"
        lines.append(
            f"- 群組 {row.get('新事業群')} / {row.get('事業群名稱', '未對應')} / "
            f"{value_column}: {format_number(row.get(value_column))} / 占比: {share_text}"
        )
    lines.append("")
    return lines


if __name__ == "__main__":
    main()
