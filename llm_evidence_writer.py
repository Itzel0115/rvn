from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from evidence_contracts import EvidenceContract
from logging_utils import get_logger


@dataclass(frozen=True)
class EvidenceWriteRequest:
    original_question: str
    canonical_task_profile: dict[str, Any]
    evidence_contracts: list[EvidenceContract]
    deterministic_display_blocks: dict[str, Any] | None = None
    required_limitations: list[str] = field(default_factory=list)
    answer_style: str = "concise"


@dataclass(frozen=True)
class EvidenceWriteResult:
    ok: bool
    output: dict[str, Any]
    error: str | None = None
    raw_response: dict[str, Any] | str | None = None


class LLMEvidenceWriter:
    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.logger = get_logger("llm_evidence_writer", request_id, domain="writer")

    def write(self, request: EvidenceWriteRequest, llm_client: Any) -> EvidenceWriteResult:
        result = llm_client.generate_json(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(request),
            temperature=0.0,
        )
        raw_response = result.data or result.text
        if not result.ok or not result.data:
            reason = result.error or "llm_evidence_writer_unavailable"
            self.logger.info("writer.shadow.fallback reason=%s", reason)
            return EvidenceWriteResult(ok=False, output={}, error=reason, raw_response=raw_response)

        output = _normalize_writer_output(result.data)
        if not output.get("headline"):
            self.logger.info("writer.shadow.fallback reason=empty_headline")
            return EvidenceWriteResult(
                ok=False,
                output=output,
                error="empty_headline",
                raw_response=raw_response,
            )
        return EvidenceWriteResult(ok=True, output=output, raw_response=raw_response)

    @staticmethod
    def _build_system_prompt() -> str:
        return (
            "You are an experimental BI evidence writer running in shadow mode. "
            "Return JSON only with keys: headline, key_observations, limitations, table_caption, confidence_note. "
            "The headline must be one sentence. Use at most 3 key_observations. "
            "Use only numbers, months, entities, and metrics present in the EvidenceContract input. "
            "Never invent numbers; if describing a table, say the table lists the evidence and do not create statistics. "
            "Do not change months. Do not rename entities. Do not change metrics. "
            "Absolutely never output source_tool, tool_name, get_*, internal function names, or any implementation detail. "
            "If an EvidenceContract contains source_tool, treat it as internal provenance only and never mention it. "
            "For task_family=forecast_unsupported, refuse safely: the headline must say 無法判斷 or 無法預測. "
            "For forecast_unsupported, never write 可能改善, 預期, 會, 將會, will improve, or any predictive claim. "
            "Do not claim root cause. If a metric is a proxy or score, call it a proxy or scorecard. "
            "Preserve the meaning of all limitations. "
            "Do not output debug strings such as table rows=9."
        )

    @staticmethod
    def _build_user_prompt(request: EvidenceWriteRequest) -> str:
        evidence_payload = [contract.to_dict() for contract in request.evidence_contracts]
        payload = {
            "original_question": request.original_question,
            "canonical_task_profile": request.canonical_task_profile,
            "evidence_contracts": evidence_payload,
            "deterministic_display_blocks": request.deterministic_display_blocks or {},
            "required_limitations": request.required_limitations,
            "answer_style": request.answer_style,
            "output_schema": {
                "headline": "string",
                "key_observations": ["string", "string", "string"],
                "limitations": ["string"],
                "table_caption": "string",
                "confidence_note": "string",
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)


def _normalize_writer_output(data: dict[str, Any]) -> dict[str, Any]:
    observations = data.get("key_observations") or []
    limitations = data.get("limitations") or []
    if not isinstance(observations, list):
        observations = [str(observations)]
    if not isinstance(limitations, list):
        limitations = [str(limitations)]
    return {
        "headline": str(data.get("headline") or "").strip(),
        "key_observations": [str(item).strip() for item in observations if str(item).strip()][:3],
        "limitations": [str(item).strip() for item in limitations if str(item).strip()],
        "table_caption": str(data.get("table_caption") or "").strip(),
        "confidence_note": str(data.get("confidence_note") or "").strip(),
    }


def evidence_write_request_to_dict(request: EvidenceWriteRequest) -> dict[str, Any]:
    payload = asdict(request)
    payload["evidence_contracts"] = [contract.to_dict() for contract in request.evidence_contracts]
    return payload
