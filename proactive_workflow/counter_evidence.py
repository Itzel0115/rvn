from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

class CounterEvidenceStatus(str, Enum):
    NOT_FOUND="not_found"; NOT_AVAILABLE="not_available"; INCONCLUSIVE="inconclusive"; CONTRADICTED="contradicted"; CONFIRMED="confirmed"; WEAKENED="weakened"

@dataclass(frozen=True)
class CounterEvidenceAssessment:
    status: CounterEvidenceStatus
    search_performed: bool
    limitation: str
    confidence_cap: str

def assess_counter_evidence(status: CounterEvidenceStatus, search_performed: bool = False) -> CounterEvidenceAssessment:
    if status is CounterEvidenceStatus.NOT_FOUND and not search_performed: raise ValueError("not_found_requires_search")
    values={
        CounterEvidenceStatus.NOT_AVAILABLE:("目前工具或資料無法執行反向證據搜尋；這不代表沒有反證。","medium"),
        CounterEvidenceStatus.NOT_FOUND:("已執行合法反向證據搜尋，但未找到反向結果。","medium"),
        CounterEvidenceStatus.INCONCLUSIVE:("已取得反向證據資料，但不足以支持方向。","low"),
        CounterEvidenceStatus.CONTRADICTED:("取得與主張相反的證據，不可形成高信心結論。","low"),
        CounterEvidenceStatus.WEAKENED:("反向證據削弱主結論，需限制信心。","low"),
        CounterEvidenceStatus.CONFIRMED:("反向檢查未推翻主張，但仍為描述性結論。","medium"),
    }
    limitation, cap=values[status]; return CounterEvidenceAssessment(status,search_performed,limitation,cap)
