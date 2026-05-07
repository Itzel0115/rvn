# Phase 6 Analysis Tools

## Scope

Phase 6A adds three deterministic analysis tools to `AnalysisToolbox`:

- `get_yoy_mom_breakdown`
- `get_contribution_analysis`
- `get_inventory_turnover_proxy`

These tools expand the system's analysis depth without introducing:

- LLM-based inference
- forecasting
- root cause claims
- formal inventory turnover accounting logic

## 1. `get_yoy_mom_breakdown`

### Purpose

Provide deterministic month-over-month and, when possible, year-over-year breakdowns for:

- `revenue`
- `inventory_amount`
- `inventory_qty`

### Inputs

- `filters`
  - `month`
  - `platform`
  - `group_code`
- `metric`
  - `revenue`
  - `inventory_amount`
  - `inventory_qty`
- `dimension`
  - `platform`
  - `business_group`
  - `overall`
- `top_n`

### Output shape

Each row includes:

- `month`
- `previous_month`
- `metric`
- `dimension`
- `name`
- `platform`
- `group_code`
- `current_value`
- `previous_value`
- `mom_change`
- `mom_change_pct`
- `mom_direction`
- `yoy_available`
- `yoy_change`
- `yoy_change_pct`
- `yoy_reason`
- `severity`

### Limitation

- If prior-year same-month data is unavailable, `yoy_available=false`
- This tool only measures observed change; it does not explain causality

## 2. `get_contribution_analysis`

### Purpose

Explain which platform or business group contributed most to the current-month change versus the previous month.

### Inputs

- `filters`
  - `month`
  - `platform`
  - `group_code`
- `metric`
  - `revenue`
  - `inventory_amount`
  - `inventory_qty`
- `dimension`
  - `platform`
  - `business_group`
- `top_n`

### Output shape

- `month`
- `previous_month`
- `metric`
- `dimension`
- `total_current`
- `total_previous`
- `total_change`
- `contributors`

Each contributor includes:

- `name`
- `platform`
- `group_code`
- `current_value`
- `previous_value`
- `change`
- `change_pct`
- `contribution_pct`
- `direction`

### Limitation

- `contribution_pct` is only computed when `total_change != 0`
- This tool quantifies contribution; it does not identify root cause

## 3. `get_inventory_turnover_proxy`

### Purpose

Use existing revenue and inventory data to create a deterministic inventory-efficiency proxy.

### Inputs

- `filters`
  - `month`
  - `platform`
  - `group_code`
- `top_n`

### Output shape

Each row includes:

- `month`
- `platform`
- `group_code`
- `revenue`
- `inventory_amount`
- `inventory_qty`
- `revenue_inventory_amount_ratio`
- `revenue_inventory_qty_ratio`
- `efficiency_level`
- `risk_label`
- `limitation`

### Limitation

- `此為營收與庫存資料推導的 proxy，不等於正式庫存週轉率。`
- This tool is suitable for relative risk observation only

## Agent Usage

Phase 6A allows existing domain agents to use these tools without changing the API contract:

- trend / comparison questions can use `get_yoy_mom_breakdown`
- comparison / diagnosis questions can use `get_contribution_analysis`
- inventory / risk / diagnosis questions can use `get_inventory_turnover_proxy`

## Contract Behavior

The `answer_contract` format is unchanged.

The new tools can now support:

- trend answers with explicit MoM wording
- diagnosis answers with contribution and inventory proxy observations
- clear YoY insufficiency wording when prior-year data is unavailable

## Explicit Non-Goals

Phase 6A does not:

- perform causal inference
- forecast future performance
- claim formal inventory turnover
- replace existing anomaly logic with LLM judgment

## 4. `get_root_cause_candidates`

### Purpose

Return deterministic candidate observations for possible drivers without claiming causal root cause.

This tool aggregates existing deterministic evidence from:

- `get_yoy_mom_breakdown`
- `get_contribution_analysis`
- `get_inventory_turnover_proxy`
- `get_anomalies`
- `get_platform_ratios`

### Inputs

- `filters`
  - `month`
  - `platform`
  - `group_code`
- `metric`
  - currently `revenue`
- `top_n`

### Output shape

- `root_cause_available`
- `month`
- `metric`
- `candidates`
- `limitations`

Each candidate includes:

- `candidate_type`
- `title`
- `description`
- `supporting_tools`
- `supporting_evidence`
- `confidence`
- `direction`
- `recommended_check`
- `limitation`

### Candidate Types

- `platform_contribution`
  - identifies the platform with the largest absolute revenue contribution change
- `business_group_contribution`
  - identifies the business group with the largest absolute revenue contribution change
- `inventory_efficiency_pressure`
  - highlights low inventory-efficiency proxy observations
- `anomaly_signal`
  - highlights the strongest anomaly or proxy risk signal that should be checked

### Confidence Rule

- `medium`
  - when multiple deterministic tools support the same candidate direction
- `low`
  - when only a single tool supports the candidate

Phase 6B intentionally does not emit `high` confidence for causal language.

### Limitation

- This tool only organizes candidate observation directions
- It does not confirm root cause
- It does not forecast future performance
- It does not treat proxy signals as formal financial or operational causes

### Explicit Non-Goal

`get_root_cause_candidates` is not a causal inference engine. It is a deterministic evidence organizer for follow-up investigation only.
