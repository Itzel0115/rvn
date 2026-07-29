from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError


DEFAULT_API_URL = "http://10.8.35.35:3000/api/ask"
DEFAULT_OUT_DIR = Path("eval/agentic_acceptance")


@dataclass(frozen=True)
class Case:
    case_id: str
    family: str
    question: str
    expected: dict[str, Any] = field(default_factory=dict)
    variant_of: str | None = None


BASE_CASES: list[Case] = [
    Case("A1", "continuous_conditions", "請找出最近四個月營收持續下降的事業群，再檢查它們同期的庫存金額與庫存數量是否持續上升，依風險程度排序，並說明每個事業群是否真的符合連續條件。", {"recent_n": 4, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["filter", "trend", "cross_check", "rank"], "dimension": "business_group"}),
    Case("A2", "continuous_conditions", "請找出最近三個月同時符合營收連續上升、庫存金額連續下降、庫存數量也連續下降的事業群。如果沒有任何事業群完全符合，請明確回答沒有，並列出最接近者及其未符合的條件。", {"recent_n": 3, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["filter", "trend", "cross_check"], "dimension": "business_group"}),
    Case("B3", "topn_entity_continuity", "比較 2026 年 1 月與 2 月各事業群營收，找出營收下降幅度最大的前三名，只針對這三個事業群檢查庫存金額與庫存數量變化，最後依庫存惡化風險重新排序。", {"periods": ["2026-01", "2026-02"], "top_n": 3, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["compare", "rank", "cross_check"], "dimension": "business_group"}),
    Case("B4", "topn_entity_continuity", "請先找出最近三個月營收下降幅度最大的五個事業群，再排除資料不足者，接著檢查剩餘對象的庫存金額、庫存數量與異常訊號，最後選出風險最高的兩個並說明反證。", {"recent_n": 3, "initial_top_n": 5, "final_top_n": 2, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "risk_score"], "operations": ["filter", "rank", "exclude", "anomaly", "counter_evidence"], "dimension": "business_group"}),
    Case("C5", "management_judgement", "找出最近月份最需要管理層關注的兩個事業群，必須同時考慮營收趨勢、庫存金額、庫存數量與異常訊號，說明為何選它們，以及有哪些證據可能降低其風險判斷。", {"top_n": 2, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "risk_score"], "operations": ["trend", "cross_check", "rank", "anomaly", "counter_evidence"], "dimension": "business_group", "requires_named_selection": True, "requires_counter_evidence": True}),
    Case("C5A", "management_judgement", "請找出最近月份最需要管理層關注的兩個事業群。請先比較所有事業群，並同時考慮營收趨勢、庫存金額、庫存數量與異常訊號，再說明選出這兩個事業群的支持證據、可能反證、資料限制，以及建議管理層下一步優先確認什麼。", {"top_n": 2, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "risk_score"], "operations": ["trend", "cross_check", "rank", "anomaly", "counter_evidence", "next_action", "select"], "dimension": "business_group", "requires_named_selection": True, "requires_counter_evidence": True, "requires_recommendation": True}),
    Case("C6", "management_judgement", "哪些事業群最近營收仍在成長，但庫存風險可能惡化？請至少用庫存金額與庫存數量兩個指標交叉判斷，不要因營收成長就直接判定表現良好。", {"metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["filter", "trend", "cross_check"], "dimension": "business_group"}),
    Case("D7", "proxy_boundary", "請評估各事業群的庫存週轉狀況。若沒有銷貨成本與平均庫存，請不要稱為正式庫存週轉率；改用現有資料建立 proxy，列出公式、分子、分母、單位與限制，並排除不可比較的資料列。", {"metrics": ["revenue_inventory_amount_ratio"], "operations": ["proxy", "exclude", "limitations"], "dimension": "business_group", "proxy_allowed": True}),
    Case("D8", "capability_boundary", "請用正式庫存週轉率找出表現最差的三個事業群，不允許使用營收除以庫存等代理指標。如果目前資料不足，請直接說明缺少哪些欄位，不要改用 proxy。", {"top_n": 3, "operations": ["capability_boundary"], "dimension": "business_group", "proxy_allowed": False}),
    Case("D9", "proxy_boundary", "請找出營收／庫存金額 proxy 最弱的三個可比較事業群，再檢查這三個事業群的庫存數量是否也支持相同風險排序。如果排序不一致，請解釋差異。", {"top_n": 3, "metrics": ["revenue_inventory_amount_ratio", "inventory_qty"], "operations": ["proxy", "rank", "cross_check"], "dimension": "business_group", "proxy_allowed": True}),
    Case("D10", "proxy_boundary", "請檢查是否有事業群因營收為負值，導致營收／庫存 proxy 失去一般效率解釋。請將這些事業群與正常可比較排名分開呈現。", {"metrics": ["revenue_inventory_amount_ratio", "revenue_amount"], "operations": ["proxy", "exclude"], "dimension": "business_group", "proxy_allowed": True}),
    Case("E11", "field_mapping", "請列出 2026 年 2 月所有事業群的營收、庫存金額與庫存數量，並標示哪些資料只存在於營收或只存在於庫存。不要把有名稱的事業群顯示成 N/A。", {"periods": ["2026-02"], "metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["filter"], "dimension": "business_group"}),
    Case("E12", "dimension_drilldown", "請以五大產品線為分析維度，找出最近三個月營收下降最多的三個產品線，再比較它們的庫存金額與庫存數量變化。", {"recent_n": 3, "top_n": 3, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["trend", "rank", "compare"], "dimension": "product_line_5"}),
    Case("E13", "dimension_drilldown", "在『1網通+技鋼』事業群內，找出最近月份營收下降但庫存金額上升的產品線，並用庫存數量作為第二項交叉證據。", {"metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["filter", "cross_check"], "dimension": "product_line_5", "parent": "1網通+技鋼"}),
    Case("E14", "field_mapping", "比較 2026 年 1 月與 2 月『3通路方案』的營收、庫存金額與庫存數量，請在同一張表中列出前期、後期、絕對變化與變化率。", {"periods": ["2026-01", "2026-02"], "metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["compare"], "dimension": "business_group", "entity": "3通路方案"}),
    Case("F15", "replan_conflict", "找出庫存風險最明顯的事業群。若第一個分析結果缺少庫存數量或異常證據，請補查其他可用工具後再回答，不要只使用現有的部分證據。", {"metrics": ["inventory_amount", "inventory_qty", "risk_score"], "operations": ["rank", "anomaly"], "dimension": "business_group"}),
    Case("F16", "replan_conflict", "如果某個事業群的庫存金額上升，但庫存數量下降，請找出這類案例，說明兩個指標為何可能方向不同，並避免只依單一指標給出結論。", {"metrics": ["inventory_amount", "inventory_qty"], "operations": ["filter", "cross_check", "limitations"], "dimension": "business_group"}),
    Case("G17", "semantic_generalization", "最近幾個月有沒有哪個事業群是東西越堆越多，但營收卻一直往下掉？幫我找出來，並確認是庫存金額和數量都變差，還是只有其中一個。", {"metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["filter", "trend", "cross_check"], "dimension": "business_group"}),
    Case("G18", "semantic_generalization", "請辨識需求動能轉弱但資金持續沉澱於庫存的事業群，並區分庫存價值增加與實體數量增加所反映的不同風險。", {"metrics": ["revenue_amount", "inventory_amount", "inventory_qty"], "operations": ["filter", "trend", "cross_check"], "dimension": "business_group"}),
    Case("G19", "semantic_generalization", "Find the top 3 business groups with declining revenue momentum, then cross-check inventory amount, inventory quantity and anomaly signals. Rank them by management risk and include counter-evidence.", {"top_n": 3, "metrics": ["revenue_amount", "inventory_amount", "inventory_qty", "risk_score"], "operations": ["trend", "rank", "cross_check", "anomaly", "counter_evidence"], "dimension": "business_group"}),
    Case("H20", "capability_boundary", "請比較各事業群毛利率、營業利益率與庫存週轉天數，找出財務體質最差的前三名。", {"top_n": 3, "operations": ["capability_boundary"], "dimension": "business_group", "unsupported_metrics": ["gross_margin", "operating_margin", "inventory_days"]}),
    Case("H21", "capability_boundary", "哪個事業群是因為產品賣不出去才造成庫存增加？請給我確定答案。", {"operations": ["capability_boundary", "counter_evidence"], "dimension": "business_group", "no_root_cause_claim": True}),
    Case("H22", "capability_boundary", "根據目前資料精準預測各事業群未來三個月營收，並保證誤差小於 5%。", {"operations": ["capability_boundary"], "dimension": "business_group", "forecast_forbidden": True}),
]


METAMORPHIC_CASES: list[Case] = [
    Case("B3-P1", "topn_entity_continuity", "請用 2026/01 到 2026/02 的各事業群營收變化，挑出跌最多的 3 個，後續只看這 3 個的庫存金額與庫存數量，並按庫存惡化風險排序。", BASE_CASES[2].expected, "B3"),
    Case("B3-P2", "topn_entity_continuity", "For Jan versus Feb 2026, rank the three business groups with the largest revenue decline, then evaluate only those same groups on inventory amount and quantity risk.", BASE_CASES[2].expected, "B3"),
    Case("C5-P1", "management_judgement", "最近月份請選出兩個最值得管理層盯緊的事業群，評估要包含營收趨勢、庫存金額、庫存數量和異常訊號，也請列出降低風險判斷的證據。", BASE_CASES[4].expected, "C5"),
    Case("C5-P2", "management_judgement", "Which two business groups need the most management attention in the latest month when revenue trend, inventory amount, inventory quantity and anomalies are all considered? Include counter-evidence.", BASE_CASES[4].expected, "C5"),
    Case("D7-P1", "proxy_boundary", "請看各事業群庫存週轉表現；若缺 COGS 與平均庫存，不要叫正式週轉率，請用現有欄位做 proxy，並列清楚公式、分子分母、單位、不可比較列與限制。", BASE_CASES[6].expected, "D7"),
    Case("D7-P2", "proxy_boundary", "Evaluate inventory turnover by business group using a proxy only if formal COGS and average inventory are unavailable; show formula, numerator, denominator, units, limits, and excluded non-comparable rows.", BASE_CASES[6].expected, "D7"),
    Case("E12-P1", "dimension_drilldown", "用產品線維度看最近 3 個月，找營收衰退最大的前三條產品線，再對照它們的庫存金額和庫存數量。", BASE_CASES[11].expected, "E12"),
    Case("E12-P2", "dimension_drilldown", "Across product_line_5, identify the top 3 product lines by revenue decline over the latest three months and compare their inventory amount and inventory quantity changes.", BASE_CASES[11].expected, "E12"),
    Case("G17-P1", "semantic_generalization", "最近有沒有事業群營收一路變弱、庫存卻越積越高？請分辨是庫存金額、庫存數量都惡化，還是只有一邊惡化。", BASE_CASES[16].expected, "G17"),
    Case("G17-P2", "semantic_generalization", "Find business groups where recent revenue keeps dropping while stock keeps building up; confirm whether both inventory amount and quantity worsen or only one does.", BASE_CASES[16].expected, "G17"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--case", action="append", help="Run only selected case ids.")
    parser.add_argument("--no-llm-planner", action="store_true")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cases = [*BASE_CASES, *METAMORPHIC_CASES]
    if args.case:
        selected = set(args.case)
        cases = [case for case in cases if case.case_id in selected]

    jsonl_path = out_dir / f"agentic_acceptance_{run_id}.jsonl"
    results: list[dict[str, Any]] = []
    try:
        for index, case in enumerate(cases, start=1):
            print(f"[{index}/{len(cases)}] {case.case_id} start", flush=True)
            result = run_case(case, args.api_url, use_llm_planner=not args.no_llm_planner, timeout=args.timeout)
            results.append(result)
            with jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            print(
                f"[{index}/{len(cases)}] {case.case_id} {result['verdict']} "
                f"{result['elapsed_seconds']}s {result.get('request_id')} {result.get('failure_reason')}",
                flush=True,
            )
    except KeyboardInterrupt:
        print("interrupted; writing partial report", flush=True)
    stats = build_stats(results)
    payload = {"run_id": run_id, "api_url": args.api_url, "stats": stats, "results": results}

    json_path = out_dir / f"agentic_acceptance_{run_id}.json"
    md_path = out_dir / f"agentic_acceptance_{run_id}.md"
    latest_json = out_dir / "latest.json"
    latest_md = out_dir / "latest.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if not jsonl_path.exists():
        jsonl_path.write_text("", encoding="utf-8")
    md = render_markdown(payload)
    md_path.write_text(md, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    return 0 if stats["fail"] == 0 and stats["partial"] == 0 else 1


def run_case(case: Case, api_url: str, *, use_llm_planner: bool, timeout: int) -> dict[str, Any]:
    started = time.perf_counter()
    status = None
    raw: dict[str, Any] | None = None
    error = None
    try:
        status, raw = post_json(api_url, {"question": case.question, "use_llm_planner": use_llm_planner}, timeout=timeout)
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - started
    response = raw or {}
    trace = extract_trace(response)
    checks = acceptance_checks(case, response, status, error)
    verdict = checks["verdict"]
    return {
        "case_id": case.case_id,
        "variant_of": case.variant_of,
        "canonical_task_family": (response.get("task_profile") or {}).get("task_family") or ((response.get("agent_state_summary") or {}).get("canonical_task") or {}).get("task_family"),
        "task_family": case.family,
        "question": case.question,
        "request_id": response.get("request_id"),
        "elapsed_seconds": round(elapsed, 3),
        "http_status": status,
        "expected_manifest": case.expected,
        "task_requirement_manifest": (response.get("task_profile") or {}).get("task_requirements") or ((response.get("agent_state_summary") or {}).get("canonical_task") or {}).get("task_requirements") or {},
        "planner_called": trace["planner_called"],
        "planner_valid": trace["planner_valid"],
        "planner_fallback_reason": trace["planner_fallback_reason"],
        "planning_source": trace["planning_source"],
        "initial_plan_steps": trace["initial_plan_steps"],
        "repaired_or_replanned_steps": trace["repaired_or_replanned_steps"],
        "executed_tools": trace["executed_tools"],
        "step_status": trace["step_status"],
        "replan_count": trace["replan_count"],
        "stop_reason": trace["stop_reason"],
        "evidence_contracts": extract_evidence_contracts(response),
        "evidence_coverage_checklist": checks["coverage"],
        "entity_sets": extract_entity_sets(response),
        "final_answer": response.get("summary") or (response.get("answer_contract") or {}).get("answer"),
        "automatic_acceptance_checks": checks["checks"],
        "verdict": verdict,
        "failure_reason": checks["failure_reason"],
        "response_error": error or response.get("error"),
    }


def post_json(url: str, payload: dict[str, Any], *, timeout: int) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        return int(resp.status), json.loads(resp.read().decode("utf-8"))


def extract_trace(response: dict[str, Any]) -> dict[str, Any]:
    runtime = response.get("agent_runtime") or {}
    state = response.get("agent_state_summary") or {}
    steps = state.get("steps") or runtime.get("steps") or []
    planning_source = runtime.get("planning_source") or state.get("planning_source") or (response.get("routing") or {}).get("planning_source")
    planner_called = planning_source in {"llm_planner", "rejected_llm_then_deterministic", "llm_then_deterministic_repair"} or str(planning_source or "").startswith("llm")
    planner_valid = planning_source == "llm_planner"
    fallback_reason = None
    if planning_source in {"rejected_llm_then_deterministic", "llm_then_deterministic_repair"}:
        issues = state.get("validation_issues") or []
        fallback_reason = issues[0] if issues else "planner_or_evidence_repair"
    return {
        "planner_called": planner_called,
        "planner_valid": planner_valid,
        "planner_fallback_reason": fallback_reason,
        "planning_source": planning_source,
        "initial_plan_steps": [step for step in steps if int(step.get("plan_version") or 1) == 1],
        "repaired_or_replanned_steps": [step for step in steps if int(step.get("plan_version") or 1) > 1],
        "executed_tools": [step.get("tool_name") for step in steps],
        "step_status": [{"step_id": step.get("step_id"), "tool": step.get("tool_name"), "status": step.get("status"), "args": step.get("tool_args") or {}} for step in steps],
        "replan_count": runtime.get("replan_count", state.get("replan_count", 0)),
        "stop_reason": runtime.get("stop_reason") or state.get("stop_reason") or response.get("stop_reason"),
    }


def extract_evidence_contracts(response: dict[str, Any]) -> list[dict[str, Any]]:
    role = response.get("answer_contract", {}).get("role_based_evidence", {}).get("evidence") or response.get("role_based_evidence", {}).get("evidence") or []
    if role:
        return role
    evidence = []
    for item in response.get("answer_contract", {}).get("evidence") or []:
        details = item.get("details") or {}
        evidence.append({"source_tool": details.get("source_tool"), "evidence_type": details.get("evidence_type"), "details": details})
    return evidence


def extract_entity_sets(response: dict[str, Any]) -> list[dict[str, Any]]:
    sets: list[dict[str, Any]] = []
    for evidence in extract_evidence_contracts(response):
        details = evidence.get("details") or evidence
        rows = details.get("rows") or []
        entities = sorted({str(row.get("entity_value")) for row in rows if isinstance(row, dict) and row.get("entity_value") is not None})
        if entities:
            sets.append({
                "source_tool": details.get("source_tool"),
                "metric": details.get("metric"),
                "entity_dimension": details.get("entity_dimension"),
                "count": len(entities),
                "entities": entities,
            })
    return sets


def acceptance_checks(case: Case, response: dict[str, Any], status: int | None, error: str | None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    manifest = (response.get("task_profile") or {}).get("task_requirements") or ((response.get("agent_state_summary") or {}).get("canonical_task") or {}).get("task_requirements") or {}
    task_profile = response.get("task_profile") or {}
    trace = extract_trace(response)
    evidence = extract_evidence_contracts(response)
    final_text = json.dumps(response.get("answer_contract", {}).get("display_blocks") or response.get("display_blocks") or {}, ensure_ascii=False) + "\n" + str(response.get("summary") or "")

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("http_200", status == 200 and not error, error or str(status))
    add("no_internal_error_code", "llm_plan_rejected:" not in final_text and "invalid_replan:" not in final_text)
    add("completed_requires_evidence", trace["stop_reason"] != "completed" or bool(evidence))
    add("no_wrong_na_for_named_entity", not _has_bad_na(response))

    expected = case.expected
    for metric in expected.get("metrics") or []:
        add(f"manifest_metric:{metric}", metric in (manifest.get("requested_metrics") or []), str(manifest.get("requested_metrics")))
        add(f"evidence_metric:{metric}", evidence_covers_metric(evidence, metric), "")
    for op in expected.get("operations") or []:
        if op == "capability_boundary":
            continue
        add(f"manifest_operation:{op}", op in (manifest.get("requested_operations") or []) or op_alias_ok(op, manifest), str(manifest.get("requested_operations")))
    if expected.get("dimension"):
        dim = expected["dimension"]
        add("manifest_dimension", dim in (manifest.get("requested_dimensions") or []) or task_profile.get("target_entity", {}).get("dimension") == dim, str(manifest.get("requested_dimensions")))
        add("evidence_dimension", not evidence or any((ev.get("details") or ev).get("entity_dimension") == dim for ev in evidence if (ev.get("details") or ev).get("entity_dimension")), dim)
    if expected.get("parent"):
        parent = expected["parent"]
        add("parent_filter_preserved", parent in json.dumps(response, ensure_ascii=False), parent)
    if expected.get("recent_n"):
        add("recent_n", int(((manifest.get("time_scope") or {}).get("recent_n") or 0)) == int(expected["recent_n"]), str(manifest.get("time_scope")))
    if expected.get("top_n"):
        add("top_n", manifest.get("top_n") == expected["top_n"], str(manifest.get("top_n")))
        add("requested_top_n", manifest.get("requested_top_n", manifest.get("top_n")) == expected["top_n"], str(manifest.get("requested_top_n")))
    if expected.get("periods"):
        text = json.dumps(response, ensure_ascii=False)
        for period in expected["periods"]:
            add(f"period:{period}", period in text, "")
    if expected.get("proxy_allowed") is False:
        add("proxy_not_used_when_forbidden", "get_inventory_turnover_proxy" not in trace["executed_tools"], str(trace["executed_tools"]))
    if expected.get("proxy_allowed") is True:
        add("proxy_tool_used", "get_inventory_turnover_proxy" in trace["executed_tools"] or evidence_covers_metric(evidence, "revenue_inventory_amount_ratio"), str(trace["executed_tools"]))
    if expected.get("forecast_forbidden"):
        add("forecast_not_overclaimed", any(token in final_text for token in ["無法", "不能", "不支援", "不足", "無法保證"]), final_text[:200])
    if expected.get("no_root_cause_claim"):
        add("no_certain_root_cause_claim", not any(token in final_text for token in ["確定是因為", "證實是因為", "必然是"]), final_text[:200])
    if case.family == "capability_boundary":
        add("capability_gap_answered", trace["stop_reason"] == "capability_gap" or any(token in final_text for token in ["缺少", "不支援", "無法", "不能", "資料不足"]), final_text[:200])
    if expected.get("requires_named_selection"):
        top_n = int(expected.get("top_n") or expected.get("final_top_n") or 0)
        selected = selected_entities_from_answer(response, top_n)
        add("answer_named_selection_count", len(selected) == top_n, str(selected))
        add("answer_has_ranking", has_ranking_language(final_text), final_text[:240])
        add("manifest_requires_named_selection", bool(manifest.get("requires_named_selection")), str(manifest))
    if expected.get("requires_counter_evidence") or case.family in {"topn_entity_continuity", "management_judgement"}:
        add("has_counter_or_risk_context", "反證" in final_text or "counter" in final_text.lower() or "異常" in final_text or "風險" in final_text, final_text[:240])
        if expected.get("requires_counter_evidence"):
            add("answer_has_counter_evidence", "反證" in final_text or "counter" in final_text.lower(), final_text[:240])
            add("manifest_requires_counter_evidence", bool(manifest.get("requires_counter_evidence")), str(manifest))
    if expected.get("requires_recommendation"):
        add("answer_has_next_action", any(token in final_text for token in ["下一步", "優先確認", "管理層下一步", "先核對", "先追查", "next action", "next step"]), final_text[:300])
        add("manifest_requires_recommendation", bool(manifest.get("requires_recommendation")), str(manifest))
    if expected.get("requires_named_selection") or expected.get("requires_recommendation"):
        add("not_generic_multimetric_headline", "已覆蓋指標" not in final_text[:500] and "已依使用者要求用多個指標" not in final_text[:500], final_text[:300])
    add("complex_has_planning_or_repair", trace["planner_called"] or trace["planning_source"] in {"deterministic", "validated_deterministic_repair", "rejected_llm_then_deterministic", "llm_then_deterministic_repair"}, str(trace["planning_source"]))

    failed = [check for check in checks if not check["ok"]]
    coverage = {
        "requested_metrics": {metric: evidence_covers_metric(evidence, metric) for metric in (manifest.get("requested_metrics") or [])},
        "requested_operations": {op: any(check["name"] == f"manifest_operation:{op}" and check["ok"] for check in checks) for op in (manifest.get("requested_operations") or [])},
        "evidence_count": len(evidence),
    }
    if not failed:
        verdict = "PASS"
        reason = ""
    elif error or status != 200 or any(item["name"] == "completed_requires_evidence" for item in failed):
        verdict = "FAIL"
        reason = "; ".join(f"{item['name']}={item['detail']}" for item in failed[:5])
    else:
        verdict = "PARTIAL"
        reason = "; ".join(f"{item['name']}={item['detail']}" for item in failed[:5])
    return {"checks": checks, "coverage": coverage, "verdict": verdict, "failure_reason": reason}


def selected_entities_from_answer(response: dict[str, Any], top_n: int) -> list[str]:
    display = response.get("answer_contract", {}).get("display_blocks") or response.get("display_blocks") or {}
    rows = ((display.get("table") or {}).get("rows") or []) if isinstance(display, dict) else []
    ranked: list[tuple[int, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        entity = row.get("entity_value") or row.get("business_group") or row.get("platform")
        rank = row.get("rank")
        if entity and rank is not None:
            try:
                ranked.append((int(rank), str(entity)))
            except (TypeError, ValueError):
                pass
    if ranked:
        return [entity for _, entity in sorted(ranked)[:top_n]]
    text = json.dumps(display, ensure_ascii=False) + "\n" + str(response.get("summary") or "")
    candidates = []
    for marker in ["第一優先事業群是", "第二優先事業群是", "第一優先事業群", "第二優先事業群"]:
        if marker in text:
            suffix = text.split(marker, 1)[1].strip()
            entity = suffix.split("：", 1)[0].split("；", 1)[0].split("。", 1)[0].strip()
            if entity:
                candidates.append(entity)
    return list(dict.fromkeys(candidates))[:top_n]


def has_ranking_language(text: str) -> bool:
    return any(token in text for token in ["第一優先", "第二優先", "第 1", "第 2", "rank", "排序", "排名"])


def op_alias_ok(op: str, manifest: dict[str, Any]) -> bool:
    operations = set(manifest.get("requested_operations") or [])
    aliases = {
        "exclude": {"filter", "limitations"},
        "capability_boundary": {"limitations"},
        "drill_down": {"filter"},
    }
    return bool(operations.intersection(aliases.get(op, set())))


def evidence_covers_metric(evidence: list[dict[str, Any]], metric: str) -> bool:
    if metric == "risk_score":
        return any((ev.get("details") or ev).get("source_tool") in {"get_anomalies", "get_entity_performance_snapshot"} or (ev.get("details") or ev).get("evidence_type") == "anomaly" for ev in evidence)
    for ev in evidence:
        details = ev.get("details") or ev
        if details.get("metric") == metric:
            return True
        if details.get("source_tool") == "get_entity_performance_snapshot" and metric in {"revenue_amount", "inventory_amount", "inventory_qty", "revenue_inventory_amount_ratio"}:
            return True
        if details.get("source_tool") == "get_revenue_inventory_relationship" and metric in {"revenue_amount", "inventory_amount", "revenue_inventory_amount_ratio"}:
            return True
        if details.get("source_tool") == "get_inventory_turnover_proxy" and metric in {"revenue_inventory_amount_ratio", "inventory_amount", "inventory_qty"}:
            return True
    return False


def _has_bad_na(response: dict[str, Any]) -> bool:
    text = json.dumps(response.get("answer_contract", {}).get("display_blocks") or response.get("display_blocks") or {}, ensure_ascii=False)
    return any(token in text for token in ["事業群 N/A", "產品線 N/A", "\"事業群\":\"N/A\"", "\"產品線\":\"N/A\""])


def build_stats(results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [item["elapsed_seconds"] for item in results]
    pass_count = sum(1 for item in results if item["verdict"] == "PASS")
    partial_count = sum(1 for item in results if item["verdict"] == "PARTIAL")
    fail_count = sum(1 for item in results if item["verdict"] == "FAIL")
    planner_called = [item for item in results if item["planner_called"]]
    planner_valid = [item for item in planner_called if item["planner_valid"]]
    repaired = [item for item in results if item["planning_source"] in {"rejected_llm_then_deterministic", "llm_then_deterministic_repair"} or item["replan_count"]]
    capability = [item for item in results if item["task_family"] == "capability_boundary"]
    return {
        "total": len(results),
        "pass": pass_count,
        "partial": partial_count,
        "fail": fail_count,
        "llm_plan_direct_valid_rate": round(len(planner_valid) / len(planner_called), 3) if planner_called else 0.0,
        "validated_repair_rate": round(len([item for item in repaired if item["verdict"] == "PASS"]) / len(repaired), 3) if repaired else 0.0,
        "replan_success_rate": round(len([item for item in results if item["replan_count"] and item["verdict"] == "PASS"]) / len([item for item in results if item["replan_count"]]), 3) if any(item["replan_count"] for item in results) else 0.0,
        "capability_gap_correctness": round(len([item for item in capability if item["verdict"] == "PASS"]) / len(capability), 3) if capability else 0.0,
        "paraphrase_stability": paraphrase_stability(results),
        "average_latency_seconds": round(statistics.mean(latencies), 3) if latencies else 0,
        "p95_latency_seconds": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 3) if latencies else 0,
    }


def paraphrase_stability(results: list[dict[str, Any]]) -> float:
    by_id = {item["case_id"]: item for item in results}
    variants = [item for item in results if item.get("variant_of")]
    if not variants:
        return 0.0
    stable = 0
    for item in variants:
        base = by_id.get(item["variant_of"])
        if not base:
            continue
        base_manifest = base.get("task_requirement_manifest") or {}
        manifest = item.get("task_requirement_manifest") or {}
        same_dim = set(base_manifest.get("requested_dimensions") or []) == set(manifest.get("requested_dimensions") or [])
        same_metrics = set(base_manifest.get("requested_metrics") or []) == set(manifest.get("requested_metrics") or [])
        stable += int(same_dim and same_metrics and item["verdict"] != "FAIL")
    return round(stable / len(variants), 3)


def render_markdown(payload: dict[str, Any]) -> str:
    stats = payload["stats"]
    lines = [
        "# Agentic Acceptance Report",
        "",
        f"- Run ID: `{payload['run_id']}`",
        f"- API URL: `{payload['api_url']}`",
        f"- Total: {stats['total']} PASS: {stats['pass']} PARTIAL: {stats['partial']} FAIL: {stats['fail']}",
        f"- LLM plan direct-valid rate: {stats['llm_plan_direct_valid_rate']}",
        f"- Validated repair rate: {stats['validated_repair_rate']}",
        f"- Replan success rate: {stats['replan_success_rate']}",
        f"- Capability gap correctness: {stats['capability_gap_correctness']}",
        f"- Paraphrase stability: {stats['paraphrase_stability']}",
        f"- Latency average / p95: {stats['average_latency_seconds']}s / {stats['p95_latency_seconds']}s",
        "",
        "| Case | Verdict | Request | Elapsed | Planner | Source | Tools | Replan | Stop | Failure |",
        "| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |",
    ]
    for item in payload["results"]:
        tools = ", ".join(dict.fromkeys(str(tool) for tool in item["executed_tools"] if tool))
        planner = "valid" if item["planner_valid"] else ("called" if item["planner_called"] else "not-called")
        failure = (item["failure_reason"] or "").replace("|", "\\|")
        lines.append(
            f"| {item['case_id']} | {item['verdict']} | `{item.get('request_id')}` | {item['elapsed_seconds']} | {planner} | {item.get('planning_source')} | {tools} | {item['replan_count']} | {item.get('stop_reason')} | {failure} |"
        )
    lines.append("")
    for item in payload["results"]:
        lines.extend([
            f"## {item['case_id']} {item['verdict']}",
            "",
            f"- Request ID: `{item.get('request_id')}`",
            f"- Family: `{item['task_family']}` / Canonical: `{item.get('canonical_task_family')}`",
            f"- Planner: called={item['planner_called']} valid={item['planner_valid']} source={item.get('planning_source')} fallback={item.get('planner_fallback_reason')}",
            f"- Replan: count={item['replan_count']} stop={item.get('stop_reason')}",
            f"- Tools: {', '.join(dict.fromkeys(str(tool) for tool in item['executed_tools'] if tool))}",
            f"- Evidence coverage: `{json.dumps(item['evidence_coverage_checklist'], ensure_ascii=False)}`",
            f"- Entity sets: `{json.dumps(item['entity_sets'], ensure_ascii=False)[:1000]}`",
            f"- Failure reason: {item['failure_reason'] or 'none'}",
            "",
        ])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
