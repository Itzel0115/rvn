from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SCHEMA_VERSION = "proactive-workflow.v1"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class Severity(str, Enum):
    INFO="info"; LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"
class ApprovalStatus(str, Enum):
    PENDING="pending"; APPROVED="approved"; REJECTED="rejected"; REVISION_REQUESTED="revision_requested"; CANCELLED="cancelled"; EXPIRED="expired"
class DraftStatus(str, Enum):
    DRAFT="draft"; REVISION_REQUESTED="revision_requested"; SUPERSEDED="superseded"; APPROVED="approved"; REJECTED="rejected"; CANCELLED="cancelled"

@dataclass
class DataRefreshEvent:
    event_id: str; dataset_ids: list[str]; trigger_source: str; current_fingerprint: dict[str, Any]
    previous_fingerprint: dict[str, Any] | None = None; changed: bool = True; change_summary: dict[str, Any] = field(default_factory=dict)
    available_period_start: str | None = None; available_period_end: str | None = None; latest_available_period: str | None = None
    data_contract_ids: list[str] = field(default_factory=list); quality_status: str = "pending"; status: str = "created"
    schema_version: str = SCHEMA_VERSION; detected_at: str = field(default_factory=utc_now)

@dataclass
class DataQualityFinding:
    finding_id: str; dataset_id: str; check_id: str; severity: Severity; status: str; description: str
    affected_scope: dict[str, Any] = field(default_factory=dict); evidence_summary: dict[str, Any] = field(default_factory=dict)
    suggested_action: str = "review"; blocks_investigation: bool = False; limitations: list[str] = field(default_factory=list)

@dataclass
class InvestigationCandidate:
    candidate_id: str; event_id: str; candidate_type: str; title: str; description: str
    metric_ids: list[str]; dimension_ids: list[str]; entity_scope: dict[str, Any]; period_scope: dict[str, Any]
    detector_id: str; detector_version: str; priority_score: float = 0.0; severity: Severity = Severity.LOW; confidence: str = "low"
    supporting_signals: list[dict[str, Any]] = field(default_factory=list); counter_signals: list[dict[str, Any]] = field(default_factory=list)
    required_task_type: str = "metric_relationship_analysis"; semantic_requirement_id: str | None = None
    deduplication_key: str = ""; status: str = "detected"; limitations: list[str] = field(default_factory=list)
    threshold_version: str = "proactive-policy.v1"; prioritization_explanation: list[str] = field(default_factory=list)

@dataclass
class InvestigationRun:
    investigation_id: str; candidate_id: str; event_id: str; agent_request_id: str; status: str
    canonical_task_summary: dict[str, Any] = field(default_factory=dict); semantic_requirement_id: str | None = None
    agent_runtime_status: str | None = None; stop_reason: str | None = None; evidence_summary: list[dict[str, Any]] = field(default_factory=list)
    counter_evidence_summary: dict[str, Any] = field(default_factory=dict); limitations: list[str] = field(default_factory=list)
    confidence: str = "low"; draft_id: str | None = None; approval_request_id: str | None = None
    started_at: str = field(default_factory=utc_now); finished_at: str | None = None

@dataclass
class ExecutiveDraft:
    draft_id: str; investigation_id: str; version: int; title: str; executive_summary: str
    key_findings: list[str] = field(default_factory=list); evidence_points: list[dict[str, Any]] = field(default_factory=list)
    counter_evidence: dict[str, Any] = field(default_factory=dict); limitations: list[str] = field(default_factory=list)
    confidence: str = "low"; recommended_followups: list[str] = field(default_factory=list)
    status: DraftStatus = DraftStatus.DRAFT; created_at: str = field(default_factory=utc_now); updated_at: str = field(default_factory=utc_now)
    markdown_path: str | None = None; json_path: str | None = None; content_hash: str = ""; supersedes_draft_id: str | None = None
    def payload_for_hash(self) -> dict[str, Any]:
        value = to_dict(self); value.pop("content_hash", None); value.pop("markdown_path", None); value.pop("json_path", None); return value
    def refresh_hash(self) -> None: self.content_hash = stable_hash(self.payload_for_hash()); self.updated_at = utc_now()

@dataclass
class ApprovalRequest:
    approval_request_id: str; investigation_id: str; draft_id: str; action_type: str = "publish_local_artifact"; risk_level: Severity = Severity.MEDIUM
    status: ApprovalStatus = ApprovalStatus.PENDING; requested_at: str = field(default_factory=utc_now); decided_at: str | None = None
    requested_by: str = "proactive_workflow"; approver: str | None = None; decision: str | None = None; decision_reason: str | None = None; revision_instructions: str | None = None
    draft_content_hash: str = ""; approved_content_hash: str | None = None; identity_source: str = "unknown"; identity_verified: bool = False

@dataclass
class PublicationRecord:
    publication_id: str; approval_request_id: str; draft_id: str; status: str; content_hash: str
    artifact_paths: list[str] = field(default_factory=list); published_at: str | None = None; publisher: str | None = None; failure_reason: str | None = None

def to_dict(value: Any) -> dict[str, Any]:
    def normalize(item: Any) -> Any:
        if isinstance(item, Enum): return item.value
        if isinstance(item, dict): return {str(k): normalize(v) for k, v in item.items()}
        if isinstance(item, list): return [normalize(v) for v in item]
        return item
    return normalize(asdict(value))
