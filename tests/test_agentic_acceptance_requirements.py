from __future__ import annotations

from types import SimpleNamespace

from task_profile import build_task_profile


def _profile(question: str):
    routing = SimpleNamespace(answer_strategy="query", question_type="query", object_dimension=None)
    return build_task_profile(question, routing)


def test_management_attention_manifest_covers_risk_counter_and_top_n():
    profile = _profile("找出最近月份最需要管理層關注的兩個事業群，必須同時考慮營收趨勢、庫存金額、庫存數量與異常訊號，說明為何選它們，以及有哪些證據可能降低其風險判斷。")

    req = profile.task_requirements
    assert req["top_n"] == 2
    assert req["requested_top_n"] == 2
    assert req["requires_named_selection"] is True
    assert req["requires_counter_evidence"] is True
    assert {"revenue_amount", "inventory_amount", "inventory_qty", "risk_score"}.issubset(req["requested_metrics"])
    assert {"trend", "cross_check", "rank", "counter_evidence", "anomaly", "select"}.issubset(req["requested_operations"])


def test_management_attention_manifest_requires_next_action_when_asked():
    profile = _profile("請找出最近月份最需要管理層關注的兩個事業群。請先比較所有事業群，並同時考慮營收趨勢、庫存金額、庫存數量與異常訊號，再說明選出這兩個事業群的支持證據、可能反證、資料限制，以及建議管理層下一步優先確認什麼。")

    req = profile.task_requirements
    assert req["requested_top_n"] == 2
    assert req["requires_named_selection"] is True
    assert req["requires_counter_evidence"] is True
    assert req["requires_recommendation"] is True
    assert req["required_selected_entity_count"] == 2
    assert {"select", "rank", "counter_evidence", "next_action"}.issubset(req["requested_operations"])


def test_semantic_stock_building_declining_revenue_maps_to_relationship_task():
    profile = _profile("最近幾個月有沒有哪個事業群是東西越堆越多，但營收卻一直往下掉？幫我找出來，並確認是庫存金額和數量都變差，還是只有其中一個。")

    assert profile.task_family == "metric_relationship_analysis"
    assert profile.time_scope["recent_n"] == 3
    req = profile.task_requirements
    assert {"revenue_amount", "inventory_amount", "inventory_qty"}.issubset(req["requested_metrics"])
    assert {"trend", "filter", "cross_check", "relationship"}.issubset(req["requested_operations"])


def test_english_latest_three_months_product_line_top_n():
    profile = _profile("Across product_line_5, identify the top 3 product lines by revenue decline over the latest three months and compare their inventory amount and inventory quantity changes.")

    req = profile.task_requirements
    assert profile.task_family == "entity_trend_comparison"
    assert profile.target_entity["dimension"] == "product_line_5"
    assert profile.time_scope["recent_n"] == 3
    assert req["top_n"] == 3
    assert {"revenue_amount", "inventory_amount", "inventory_qty"}.issubset(req["requested_metrics"])


def test_formal_inventory_turnover_forbids_proxy_execution_path():
    profile = _profile("請用正式庫存週轉率找出表現最差的三個事業群，不允許使用營收除以庫存等代理指標。如果目前資料不足，請直接說明缺少哪些欄位，不要改用 proxy。")

    assert profile.task_family == "forecast_unsupported"
    assert profile.business_intent == "capability_boundary_unsupported"
    assert profile.task_requirements["top_n"] == 3


def test_chinese_product_line_dimension_does_not_extract_prompt_prefix_as_entity():
    profile = _profile("請以五大產品線為分析維度，找出最近三個月營收下降最多的三個產品線，再比較它們的庫存金額與庫存數量變化。")

    assert profile.task_family == "entity_trend_comparison"
    assert profile.target_entity == {"dimension": "product_line_5", "value": None, "scope": "all"}
    assert profile.task_requirements["top_n"] == 3
    assert {"revenue_amount", "inventory_amount", "inventory_qty"}.issubset(profile.task_requirements["requested_metrics"])


def test_english_period_pair_quantity_elision_is_inventory_qty():
    profile = _profile("For Jan versus Feb 2026, rank the three business groups with the largest revenue decline, then evaluate only those same groups on inventory amount and quantity risk.")

    assert profile.time_scope["period_a"] == "2026-01"
    assert profile.time_scope["period_b"] == "2026-02"
    assert profile.task_requirements["top_n"] == 3
    assert {"revenue_amount", "inventory_amount", "inventory_qty"}.issubset(profile.task_requirements["requested_metrics"])
    assert "cross_check" in profile.task_requirements["requested_operations"]


def test_product_line_dimension_phrase_does_not_become_business_group_entity():
    profile = _profile("用產品線維度看最近 3 個月，找營收衰退最大的前三條產品線，再對照它們的庫存金額和庫存數量。")

    assert profile.task_family == "entity_trend_comparison"
    assert profile.target_entity == {"dimension": "product_line_5", "value": None, "scope": "all"}
    assert profile.task_requirements["top_n"] == 3
    assert "compare" in profile.task_requirements["requested_operations"]
