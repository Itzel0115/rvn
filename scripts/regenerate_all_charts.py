
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis_pipeline import build_pipeline_context
from analysis_tools import AnalysisToolbox


def main() -> int:
    ctx = build_pipeline_context("regenerate-all-charts")
    toolbox = AnalysisToolbox(ctx, request_id="regenerate-all-charts")
    chart_dir = ROOT / "output" / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)

    removed = 0
    for png in chart_dir.glob("*.png"):
        png.unlink()
        removed += 1

    catalog = toolbox.get_chart_catalog()
    created: list[tuple[str, str]] = []
    skipped: list[str] = []
    failed: list[tuple[str, str]] = []

    for item in catalog:
        chart_key = str(item.get("chart_key"))
        if not item.get("available"):
            skipped.append(chart_key)
            continue
        try:
            result = toolbox.create_chart_image(chart_key)
            if result and result.get("output_path"):
                created.append((chart_key, str(result["output_path"])))
            else:
                failed.append((chart_key, "No output path returned"))
        except Exception as exc:
            failed.append((chart_key, f"{type(exc).__name__}: {exc}"))

    print(f"removed_png={removed}")
    print(f"created_count={len(created)}")
    print(f"skipped_count={len(skipped)}")
    print(f"failed_count={len(failed)}")
    for chart_key, output_path in created:
        print(f"CREATED	{chart_key}	{output_path}")
    for chart_key in skipped:
        print(f"SKIPPED	{chart_key}")
    for chart_key, message in failed:
        print(f"FAILED	{chart_key}	{message}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
