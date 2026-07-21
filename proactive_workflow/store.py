from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, TypeVar

from .models import ApprovalRequest, DataQualityFinding, DataRefreshEvent, ExecutiveDraft, InvestigationCandidate, InvestigationRun, PublicationRecord, to_dict

T = TypeVar("T")
_TABLES = {"events":"event_id", "quality_findings":"finding_id", "candidates":"candidate_id", "investigations":"investigation_id", "drafts":"draft_id", "approvals":"approval_request_id", "publications":"publication_id", "audit_events":"audit_id"}

class SQLiteProactiveStore:
    schema_version = "proactive-store.v1"
    def __init__(self, database_path: str | Path) -> None:
        self.path = Path(database_path); self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS proactive_schema (version TEXT NOT NULL)")
            connection.execute("INSERT INTO proactive_schema(version) SELECT ? WHERE NOT EXISTS (SELECT 1 FROM proactive_schema)", (self.schema_version,))
            for table, key in _TABLES.items():
                connection.execute(f"CREATE TABLE IF NOT EXISTS {table} ({key} TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)")
            connection.execute("CREATE INDEX IF NOT EXISTS candidates_dedup ON candidates(candidate_id)")
    def _connect(self) -> sqlite3.Connection: return sqlite3.connect(self.path)
    def _save(self, table: str, key: str, value: Any) -> None:
        payload = json.dumps(to_dict(value) if not isinstance(value, dict) else value, ensure_ascii=False, sort_keys=True)
        with self._connect() as connection: connection.execute(f"INSERT INTO {table} VALUES (?, ?, CURRENT_TIMESTAMP) ON CONFLICT({key}) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at", (getattr(value, key) if not isinstance(value, dict) else value[key], payload))
    def _load(self, table: str, key: str, cls: type[T]) -> T | None:
        with self._connect() as connection: row = connection.execute(f"SELECT payload FROM {table} WHERE {_TABLES[table]}=?", (key,)).fetchone()
        return _decode(json.loads(row[0]), cls) if row else None
    def _list(self, table: str, cls: type[T]) -> list[T]:
        with self._connect() as connection: rows=connection.execute(f"SELECT payload FROM {table} ORDER BY updated_at DESC").fetchall()
        return [_decode(json.loads(row[0]), cls) for row in rows]
    def save_event(self, value: DataRefreshEvent) -> None: self._save("events", "event_id", value)
    def load_event(self, key: str) -> DataRefreshEvent | None: return self._load("events", key, DataRefreshEvent)
    def get_latest_event(self) -> DataRefreshEvent | None:
        values=self._list("events", DataRefreshEvent); return values[0] if values else None
    def find_event_by_fingerprint(self, fingerprint: str) -> DataRefreshEvent | None:
        return next((item for item in self._list("events", DataRefreshEvent) if item.current_fingerprint.get("fingerprint") == fingerprint), None)
    def save_quality_finding(self, value: DataQualityFinding) -> None: self._save("quality_findings", "finding_id", value)
    def list_quality_findings(self, event_id: str | None = None) -> list[DataQualityFinding]: return self._list("quality_findings", DataQualityFinding)
    def save_candidate(self, value: InvestigationCandidate) -> None: self._save("candidates", "candidate_id", value)
    def load_candidate(self, key: str) -> InvestigationCandidate | None: return self._load("candidates", key, InvestigationCandidate)
    def list_candidates(self, event_id: str | None = None) -> list[InvestigationCandidate]:
        values=self._list("candidates", InvestigationCandidate); return [x for x in values if event_id is None or x.event_id == event_id]
    def find_candidate_by_deduplication_key(self, key: str) -> InvestigationCandidate | None:
        return next((x for x in self._list("candidates", InvestigationCandidate) if x.deduplication_key == key and x.status not in {"cancelled", "closed"}), None)
    def save_investigation(self, value: InvestigationRun) -> None: self._save("investigations", "investigation_id", value)
    def load_investigation(self, key: str) -> InvestigationRun | None: return self._load("investigations", key, InvestigationRun)
    def list_investigations(self) -> list[InvestigationRun]: return self._list("investigations", InvestigationRun)
    def save_draft(self, value: ExecutiveDraft) -> None: self._save("drafts", "draft_id", value)
    def load_draft(self, key: str) -> ExecutiveDraft | None: return self._load("drafts", key, ExecutiveDraft)
    def list_drafts(self) -> list[ExecutiveDraft]: return self._list("drafts", ExecutiveDraft)
    def save_approval_request(self, value: ApprovalRequest) -> None: self._save("approvals", "approval_request_id", value)
    def load_approval_request(self, key: str) -> ApprovalRequest | None: return self._load("approvals", key, ApprovalRequest)
    def list_pending_approvals(self) -> list[ApprovalRequest]: return [x for x in self._list("approvals", ApprovalRequest) if x.status.value == "pending"]
    def list_approvals(self) -> list[ApprovalRequest]: return self._list("approvals", ApprovalRequest)
    def save_publication(self, value: PublicationRecord) -> None: self._save("publications", "publication_id", value)
    def load_publication(self, key: str) -> PublicationRecord | None: return self._load("publications", key, PublicationRecord)
    def save_audit(self, value: dict[str, Any]) -> None: self._save("audit_events", "audit_id", value)

def _decode(data: dict[str, Any], cls: type[T]) -> T:
    from .models import ApprovalStatus, DraftStatus, Severity
    if cls is DataQualityFinding: data["severity"] = Severity(data["severity"])
    if cls is InvestigationCandidate: data["severity"] = Severity(data["severity"])
    if cls is ExecutiveDraft: data["status"] = DraftStatus(data["status"])
    if cls is ApprovalRequest: data["status"] = ApprovalStatus(data["status"]); data["risk_level"] = Severity(data["risk_level"])
    return cls(**data)
