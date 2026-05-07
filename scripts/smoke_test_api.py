from __future__ import annotations

import json

import requests


API_URL = "http://127.0.0.1:8765/api/ask"
QUESTIONS = [
    "最新月份營收最高的新事業群是誰？",
    "哪個平台庫存金額最高？",
    "最近有什麼營運風險？",
    "有沒有營收下降但庫存上升的事業群？",
    "請幫我畫營收趨勢。",
    "資料涵蓋哪些月份？",
    "為什麼營收下降？",
    "下個月營收會不會改善？",
]


def main() -> None:
    for question in QUESTIONS:
        try:
            response = requests.post(API_URL, json={"question": question}, timeout=180)
            response.raise_for_status()
            data = response.json()
            contract = data.get("answer_contract", {})
            output = {
                "question": question,
                "routing.question_type": data.get("routing", {}).get("question_type"),
                "routing.domains": data.get("routing", {}).get("domains"),
                "answer_contract.answer_type": contract.get("answer_type"),
                "tools_used": contract.get("tools_used", []),
                "evidence_count": len(contract.get("evidence", [])),
                "limitations": contract.get("limitations", []),
                "answer": contract.get("answer"),
            }
        except Exception as exc:
            output = {
                "question": question,
                "error": type(exc).__name__,
                "detail": str(exc),
            }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        print("-" * 80)


if __name__ == "__main__":
    main()
