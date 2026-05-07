from __future__ import annotations

import argparse
import json

from analysis_pipeline import build_pipeline_context
from config import OUTPUT_DIR
from logging_utils import configure_logging, get_logger
from multi_agent import MultiAgentAssistant


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-agent data analysis assistant built on the current project.")
    parser.add_argument("--question", type=str, help="Single question for the assistant to answer.")
    parser.add_argument("--project-summary", action="store_true", help="Print project understanding summary before answering.")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging.")
    parser.add_argument("--json", action="store_true", help="Print full JSON output instead of summary only.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    request_id = configure_logging(OUTPUT_DIR / "logs", debug=args.debug)
    logger = get_logger("agent_cli", request_id)
    logger.info("Starting multi-agent assistant CLI")

    context = build_pipeline_context(request_id)
    assistant = MultiAgentAssistant(context, request_id)

    if args.project_summary:
        summary = assistant.summarize_project()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not args.question:
            return

    question = args.question or input("請輸入問題: ").strip()
    if not question:
        raise SystemExit("問題不可為空。")

    response = assistant.answer(question)
    if args.json:
        print(json.dumps(response, ensure_ascii=False, indent=2))
    else:
        print(response["summary"])


if __name__ == "__main__":
    main()
