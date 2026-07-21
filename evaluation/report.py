from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import EvalCaseResult
from .scorecard import write_scorecard_artifacts


def generate_report(folder: Path, manifest: dict[str, Any], results: list[EvalCaseResult]) -> dict[str, Any]:
    return write_scorecard_artifacts(folder, manifest, results)
