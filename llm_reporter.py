from __future__ import annotations

import json
from pathlib import Path

from config import COL_ANOMALY_REASON, COL_ANOMALY_TYPE, COL_MONTH, OLLAMA_BASE_URL, OLLAMA_MODEL
from ollama_client import OllamaClient
from utils import MessageCollector


def generate_llm_explanation(report_context: dict, output_path: Path) -> MessageCollector:
    collector = MessageCollector()
    client = OllamaClient(request_id="report")
    prompt = build_prompt(report_context)
    result = client.generate(
        system_prompt=(
            "你是一位資深資料分析顧問。"
            "請根據提供的 JSON 報告內容，輸出一份條理清楚、可讀性高的 Markdown 分析報告。"
        ),
        user_prompt=prompt,
    )
    if result.ok:
        output_path.write_text(result.text, encoding="utf-8")
        collector.add_info(f"已使用 Ollama {OLLAMA_MODEL} 生成 LLM 說明報告。")
    else:
        collector.add_warning(f"Ollama 生成報告失敗，改用 fallback 說明。原因: {result.error}")
        output_path.write_text(
            build_fallback_explanation(report_context, result.error or "unknown error"),
            encoding="utf-8",
        )
    return collector


def generate_qa_llm_answer(question: str, context: dict) -> tuple[str, MessageCollector]:
    collector = MessageCollector()
    client = OllamaClient(request_id="qa")
    prompt = build_qa_prompt(question, context)
    result = client.generate(
        system_prompt=(
            "你是一位資料分析助手。"
            "請根據給你的檢索資料與程式摘要回答問題，不要捏造不存在的資料。"
        ),
        user_prompt=prompt,
    )
    if result.ok:
        return result.text, collector

    collector.add_warning(f"AI 問答失敗，改用 fallback。原因: {result.error}")
    return build_qa_ai_fallback(question, context, result.error or "unknown error"), collector


def build_prompt(report_context: dict) -> str:
    context_json = json.dumps(report_context, ensure_ascii=False, indent=2)
    return (
        "請將以下 JSON 報告內容整理成 Markdown 分析報告，至少包含：\n"
        "1. 專案與資料概況\n"
        "2. 主要發現\n"
        "3. 風險與限制\n"
        "4. 建議後續行動\n\n"
        f"{context_json}"
    )


def build_qa_prompt(question: str, context: dict) -> str:
    retrieved = context.get("retrieved_records_markdown", "- 無檢索資料")
    programmatic = context.get("programmatic_summary", "- 無程式摘要")
    return (
        "請根據下列資訊回答使用者問題。\n"
        "- 只能使用提供的資料與摘要\n"
        "- 若資料不足請直接說明限制\n"
        "- 回答請使用繁體中文\n\n"
        f"問題:\n{question}\n\n"
        f"檢索資料:\n{retrieved}\n\n"
        f"程式摘要:\n{programmatic}"
    )


def build_fallback_explanation(report_context: dict, error_message: str) -> str:
    anomalies = report_context.get("anomaly_records", [])
    anomaly_lines = "\n".join(
        f"- {item.get(COL_MONTH, 'N/A')} | {item.get(COL_ANOMALY_TYPE, 'N/A')} | {item.get(COL_ANOMALY_REASON, 'N/A')}"
        for item in anomalies[:10]
    )
    if not anomaly_lines:
        anomaly_lines = "- 目前沒有異常摘要可列出。"

    mapping_status = "成功" if report_context.get("mapping_success") else "失敗"
    merged_status = "可用" if report_context.get("merged_analysis_available") else "不可用"

    return f"""# LLM Fallback Report

Ollama 生成報告失敗，因此改用 fallback 內容。

## 系統資訊

- Ollama base URL: `{OLLAMA_BASE_URL}`
- 模型: `{OLLAMA_MODEL}`
- 錯誤: `{error_message}`

## 資料概況

- inventory_rows: {report_context.get('inventory_rows', 0)}
- revenue_rows: {report_context.get('revenue_rows', 0)}
- mapping_rows: {report_context.get('mapping_rows', 0)}
- mapping_success: {mapping_status}
- merged_analysis_available: {merged_status}

## 異常摘要

{anomaly_lines}
"""


def build_qa_ai_fallback(question: str, context: dict, error_message: str) -> str:
    summary = context.get("programmatic_summary", "目前沒有可用的程式摘要。")
    return (
        f"問題: {question}\n"
        f"AI 回答失敗原因: {error_message}\n"
        f"目前可用摘要: {summary}"
    )
