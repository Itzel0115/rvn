from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.support import build_stubbed_assistant


REPORT_DIR = PROJECT_ROOT / "eval"
CSV_FILE = REPORT_DIR / "demo_smoke_results.csv"
MD_FILE = REPORT_DIR / "demo_smoke_report.md"

DEMO_QUESTIONS = [
    "請分析哪個平台表現較佳",
    "請分析哪個平台表現較差",
    "比較 8 月各平台營收與庫存",
    "哪個平台最健康？",
    "最近有什麼營運風險？",
    "8 月相較 7 月營收變化主要由誰貢獻？",
    "資料涵蓋哪些月份？",
    "下個月營收會不會改善？",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic demo smoke questions.")
    parser.add_argument(
        "--api-url",
        default="",
        help="Optional API base URL, for example http://127.0.0.1:8765. If omitted, runs direct assistant mode.",
    )
    args = parser.parse_args()

    rows = run_api_smoke(args.api_url) if args.api_url else run_direct_smoke()
    write_csv(rows)
    write_markdown(rows, mode="api" if args.api_url else "direct")
    print(f"Wrote {CSV_FILE}")
    print(f"Wrote {MD_FILE}")


def run_direct_smoke() -> list[dict[str, Any]]:
    assistant = build_stubbed_assistant("demo-smoke", use_llm_planner=False, use_llm_rewriter=False)
    return [summarize_response(question, assistant.answer(question)) for question in DEMO_QUESTIONS]


def run_api_smoke(api_url: str) -> list[dict[str, Any]]:
    base = api_url.rstrip("/")
    rows: list[dict[str, Any]] = []
    for question in DEMO_QUESTIONS:
        body = json.dumps(
            {
                "question": question,
                "use_llm_planner": False,
                "use_llm_rewriter": False,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{base}/api/ask",
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows.append(summarize_response(question, payload))
    return rows


def summarize_response(question: str, response: dict[str, Any]) -> dict[str, Any]:
    contract = response.get("answer_contract", {}) or {}
    task_profile = response.get("task_profile", {}) or {}
    answer_plan = response.get("answer_plan", {}) or {}
    display = contract.get("display_blocks", {}) or {}
    table = display.get("table") or {}

    return {
        "question": question,
        "task_family": task_profile.get("task_family", ""),
        "primary_tools": ", ".join(answer_plan.get("primary_tools", []) or []),
        "headline": display.get("headline", ""),
        "key_observation_count": len(display.get("key_observations") or []),
        "has_table": bool(table.get("rows")),
        "limitations": " | ".join(display.get("limitations") or contract.get("limitations") or []),
        "tools_used": ", ".join(contract.get("tools_used", []) or []),
    }


def write_csv(rows: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "question",
        "task_family",
        "primary_tools",
        "headline",
        "key_observation_count",
        "has_table",
        "limitations",
        "tools_used",
    ]
    with CSV_FILE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, Any]], mode: str) -> None:
    lines = [
        "# Demo Smoke Report",
        "",
        f"- mode: {mode}",
        f"- cases: {len(rows)}",
        "",
        "| Question | Task Family | Key Obs | Table | Headline |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {question} | {task_family} | {key_observation_count} | {has_table} | {headline} |".format(
                question=_escape_md(row["question"]),
                task_family=_escape_md(row["task_family"]),
                key_observation_count=row["key_observation_count"],
                has_table="yes" if row["has_table"] else "no",
                headline=_escape_md(row["headline"]),
            )
        )

    lines.extend(["", "## Details", ""])
    for row in rows:
        lines.extend(
            [
                f"### {_escape_md(row['question'])}",
                "",
                f"- task_family: `{row['task_family']}`",
                f"- primary_tools: `{row['primary_tools']}`",
                f"- tools_used: `{row['tools_used']}`",
                f"- key_observation_count: `{row['key_observation_count']}`",
                f"- has_table: `{row['has_table']}`",
                f"- limitations: {row['limitations'] or 'none'}",
                f"- headline: {row['headline'] or 'none'}",
                "",
            ]
        )

    MD_FILE.write_text("\n".join(lines), encoding="utf-8")


def _escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    main()
