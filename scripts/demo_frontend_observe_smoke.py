from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
ROOT = Path(__file__).resolve().parents[1]


def _loads(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(
            text.replace("NaN", "null").replace("-Infinity", "null").replace("Infinity", "null")
        )


def request_json(path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Accept": "application/json"}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"

    request = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return _loads(response.read())
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {path} failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise AssertionError(f"{method} {path} failed: {exc}") from exc


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_rows(path: str, payload: dict) -> dict:
    result = request_json(path, payload)
    rows = result.get("rows") or []
    assert_true(rows, f"Expected rows for payload {payload}, got {result}")
    return result


def check_summary() -> None:
    summary = request_json("/api/summary")
    dashboard = summary.get("dashboard_snapshot") or {}
    revenue_group = ((dashboard.get("revenue_extremes") or {}).get("max") or {})
    revenue_product_line = ((dashboard.get("product_line_revenue_extremes") or {}).get("max") or {})
    inventory_product_line = ((dashboard.get("product_line_inventory_extremes") or {}).get("max") or {})

    assert_true(revenue_group.get("platform"), "summary is missing highest revenue business group")
    assert_true(
        revenue_product_line.get("product_line_5"),
        "summary is missing highest revenue product-line KPI field",
    )
    assert_true(
        inventory_product_line.get("product_line_5"),
        "summary is missing highest inventory product-line KPI field",
    )


def check_options() -> None:
    options = request_json("/api/observe-options")
    dimensions = {item.get("value") for item in options.get("row_dimensions") or []}
    metrics = {item.get("value") for item in options.get("metrics") or []}
    modes = {item.get("value") for item in options.get("compare_modes") or []}

    assert_true({"month", "business_group", "product_line_5"}.issubset(dimensions), f"Bad dimensions: {dimensions}")
    assert_true("revenue" in metrics, f"Bad metrics: {metrics}")
    assert_true("previous_period" in modes, f"Bad compare modes: {modes}")
    assert_true(options.get("business_groups"), "observe-options missing business_groups")
    assert_true(options.get("product_lines"), "observe-options missing product_lines")
    assert_true("2026-02" in (options.get("months") or []), "observe-options missing 2026-02")


def check_observe_rows() -> None:
    common = {"metric": "revenue", "compare_mode": "previous_period", "current_month": "2026-02"}
    assert_rows(
        "/api/observe",
        {**common, "row_dimension": "month", "platform": "all", "group_code": None},
    )
    assert_rows(
        "/api/observe",
        {**common, "row_dimension": "business_group", "platform": "all", "group_code": None},
    )
    assert_rows(
        "/api/observe",
        {**common, "row_dimension": "product_line", "product_line": "all"},
    )


def check_frontend_source_labels() -> None:
    insight = (ROOT / "frontend/components/insight-console.jsx").read_text(encoding="utf-8")
    kpi_utils = (ROOT / "frontend/components/kpi/kpi-utils.js").read_text(encoding="utf-8")

    assert_true("本月最高營收產品線" in insight, "desktop KPI copy missing product-line label")
    assert_true("產品線篩選" in insight, "observation filter copy missing product-line label")
    assert_true("product_line_revenue_extremes" in kpi_utils, "KPI utility is not mapped to product-line revenue extremes")


def main() -> int:
    checks = [check_summary, check_options, check_observe_rows, check_frontend_source_labels]
    for check in checks:
        check()
        print(f"ok - {check.__name__}")
    print("frontend observe smoke passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
