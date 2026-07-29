from __future__ import annotations

import argparse
import json

from analysis_pipeline import build_pipeline_context
from config import OUTPUT_DIR
from logging_utils import configure_logging, get_logger
from multi_agent import MultiAgentAssistant


def main() -> None:
    args = parse_args()
    if not (args.agent_question or args.question or args.agent_project_summary or args.project_summary):
        print("目前只支援 agent/project-summary 模式；請使用 --help 查看可用參數。")
        return

    args.agent_question = args.agent_question or args.question
    args.agent_project_summary = args.agent_project_summary or args.project_summary
    run_multi_agent_mode(args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="去識別化營收與庫存 Agent 工具")
    parser.add_argument("--agent-question", type=str, help="使用多 Agent assistant 回答單一問題")
    parser.add_argument("--question", type=str, help="--agent-question 的相容別名")
    parser.add_argument("--agent-project-summary", action="store_true", help="輸出目前專案與資料摘要")
    parser.add_argument("--project-summary", action="store_true", help="--agent-project-summary 的相容別名")
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



if __name__ == "__main__":
    main()
