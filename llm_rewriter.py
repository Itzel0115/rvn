from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from logging_utils import get_logger


FORBIDDEN_PHRASES = [
    "原因就是",
    "一定是",
    "已確認根本原因",
    "必然",
    "預測會",
    "下個月一定",
    "導致",
    "confirmed root cause",
    "will improve",
    "will decline",
]

LIMITATION_RULES = [
    {
        "label": "cannot_directly_determine",
        "source_hints": [
            "無法直接判斷",
            "尚無法直接判斷",
            "不能判定根本原因",
            "cannot directly determine",
            "cannot determine root cause",
        ],
        "required_hints": [
            "無法直接判斷",
            "尚無法直接判斷",
            "不能判定根本原因",
            "不能直接代表根本原因",
            "cannot directly determine",
            "cannot determine root cause",
        ],
    },
    {
        "label": "turnover_proxy",
        "source_hints": [
            "不等於正式庫存週轉率",
            "not equal to formal inventory turnover",
            "proxy，不等於正式庫存週轉率",
        ],
        "required_hints": [
            "不等於正式庫存週轉率",
            "正式庫存週轉率",
            "proxy",
            "not equal to formal inventory turnover",
        ],
    },
    {
        "label": "missing_operational_fields",
        "source_hints": [
            "尚未納入訂單",
            "尚未包含訂單",
            "尚未包含訂單、出貨、價格、客戶與市場需求",
            "訂單、出貨、價格、客戶與市場需求",
            "order",
            "shipment",
            "price",
            "customer",
            "market demand",
        ],
        "required_hints": [
            "訂單",
            "出貨",
            "價格",
            "客戶",
            "市場需求",
            "order",
            "shipment",
            "price",
            "customer",
            "market demand",
            "資料尚未包含",
            "尚未納入",
        ],
    },
]

NUMBER_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?%?")


@dataclass(frozen=True)
class RewriteRequest:
    question: str
    deterministic_answer: str
    answer_contract: dict[str, Any]
    evidence: list[dict[str, Any]]
    limitations: list[str]
    tools_used: list[str]


@dataclass(frozen=True)
class RewriteValidationResult:
    passed: bool
    violations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RewriteResult:
    ok: bool
    rewritten_answer: str
    validation_passed: bool
    fallback_reason: str | None = None
    raw_response: dict[str, Any] | str | None = None
    violations: list[str] = field(default_factory=list)


class LLMAnswerRewriter:
    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.logger = get_logger("llm_rewriter", request_id, domain="rewriter")

    def rewrite(self, request: RewriteRequest, llm_client: Any) -> RewriteResult:
        result = llm_client.generate_json(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(request),
            temperature=0.0,
        )
        raw_response = result.data or result.text
        if not result.ok or not result.data:
            reason = result.error or "llm_rewriter_unavailable"
            self.logger.info("rewriter.fallback reason=%s", reason)
            return RewriteResult(
                ok=False,
                rewritten_answer=request.deterministic_answer,
                validation_passed=False,
                fallback_reason="llm_rewriter_unavailable",
                raw_response=raw_response,
                violations=[reason],
            )

        rewritten_answer = str(result.data.get("rewritten_answer") or "").strip()
        if not rewritten_answer:
            self.logger.info("rewriter.fallback reason=empty_rewrite")
            return RewriteResult(
                ok=False,
                rewritten_answer=request.deterministic_answer,
                validation_passed=False,
                fallback_reason="llm_rewriter_invalid_output",
                raw_response=raw_response,
                violations=["empty_rewritten_answer"],
            )

        validation = self.validate(request, rewritten_answer)
        if not validation.passed:
            self.logger.info("rewriter.fallback reason=validation_failed violations=%s", validation.violations)
            return RewriteResult(
                ok=False,
                rewritten_answer=request.deterministic_answer,
                validation_passed=False,
                fallback_reason="llm_rewriter_validation_failed",
                raw_response=raw_response,
                violations=validation.violations,
            )

        self.logger.info("rewriter.done answer_length=%s", len(rewritten_answer))
        return RewriteResult(
            ok=True,
            rewritten_answer=rewritten_answer,
            validation_passed=True,
            raw_response=raw_response,
            violations=[],
        )

    def validate(self, request: RewriteRequest, rewritten_answer: str) -> RewriteValidationResult:
        violations: list[str] = []
        rewritten_lower = rewritten_answer.lower()

        allowed_numbers = set(_extract_numbers(request.deterministic_answer))
        allowed_numbers.update(_extract_numbers(json.dumps(request.evidence, ensure_ascii=False)))
        rewritten_numbers = _extract_numbers(rewritten_answer)
        new_numbers = [token for token in rewritten_numbers if token not in allowed_numbers]
        if new_numbers:
            violations.append(f"new_numbers={sorted(set(new_numbers))}")

        forbidden_hits = [phrase for phrase in FORBIDDEN_PHRASES if phrase.lower() in rewritten_lower]
        if forbidden_hits:
            violations.append(f"forbidden_phrases={forbidden_hits}")

        source_text = "\n".join([request.deterministic_answer, *request.limitations]).lower()
        for rule in LIMITATION_RULES:
            if any(hint.lower() in source_text for hint in rule["source_hints"]):
                if not any(hint.lower() in rewritten_lower for hint in rule["required_hints"]):
                    violations.append(f"missing_limitation:{rule['label']}")

        base_length = max(len(request.deterministic_answer.strip()), 1)
        if len(rewritten_answer.strip()) > math.ceil(base_length * 2.5):
            violations.append("rewritten_answer_too_long")

        return RewriteValidationResult(passed=not violations, violations=violations)

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "You are an answer rewriting module for a deterministic business analysis assistant. "
            "You may only rewrite tone, structure, and readability.\n"
            "Rules:\n"
            "1. Only use facts already present in the provided answer contract content.\n"
            "2. Do not add any new facts, numbers, causes, or forecasts.\n"
            "3. Do not calculate numbers.\n"
            "4. Do not say root cause is confirmed.\n"
            "5. Do not predict the future.\n"
            "6. Preserve limitation semantics when the original answer includes them.\n"
            "7. Return JSON only with one key: rewritten_answer.\n"
        )

    @staticmethod
    def _build_user_prompt(request: RewriteRequest) -> str:
        payload = {
            "question": request.question,
            "deterministic_answer": request.deterministic_answer,
            "answer_contract": request.answer_contract,
            "evidence": request.evidence,
            "limitations": request.limitations,
            "tools_used": request.tools_used,
        }
        return (
            "Rewrite the deterministic answer for readability only. "
            "Keep all facts grounded in the provided content.\n"
            f"Payload: {json.dumps(payload, ensure_ascii=False)}"
        )


def _extract_numbers(text: str) -> list[str]:
    return NUMBER_PATTERN.findall(text or "")


def build_rewrite_request(question: str, contract: dict[str, Any]) -> RewriteRequest:
    return RewriteRequest(
        question=question,
        deterministic_answer=str(contract.get("answer", "")),
        answer_contract=contract,
        evidence=list(contract.get("evidence", [])),
        limitations=[str(item) for item in contract.get("limitations", [])],
        tools_used=[str(item) for item in contract.get("tools_used", [])],
    )


def rewrite_result_payload(result: RewriteResult) -> dict[str, Any]:
    return asdict(result)
