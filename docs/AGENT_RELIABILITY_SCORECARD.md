# Agent Reliability Scorecard

The final scorecard keeps two populations separate:

- **Execution-backed Reliability (90%)**: task success 20%, evidence quality 20%, trajectory correctness 15%, tool correctness 10%, replanning quality 10%, answer grounding 10%, safety compliance 10%, and efficiency 5%.
- **Synthetic Grader Validation (10%)**: the two intentionally impossible/recorded adversarial trajectories validate deterministic grader behavior; their score cannot compensate for execution or safety failures.

The report includes declared, attempted, completed, and passed execution counts; execution pass rate; trace completeness; execution fidelity; hard-invariant rate; detailed task/evidence/tool/replan/grounding/safety rates; tool/replan efficiency; and p50/p95 duration. Token and cost values are `null` with `cost_status=local_or_unavailable` for local deterministic runs.

`execution_fidelity_rate < 1.0` or `hard_invariant_pass_rate < 1.0` forces the scorecard status to `failed`, independent of the weighted score. The strict gate additionally applies the versioned thresholds in `evaluation/policies/regression_gate.v1.json`. Expected security rejection is recorded as completed execution and is not a reliability failure.

```bash
uv run python -m evaluation.cli coverage --run-id EVAL_RUN
uv run python -m evaluation.cli report EVAL_RUN
uv run python -m evaluation.cli gate EVAL_RUN
uv run python -m evaluation.cli compare BASELINE_RUN CANDIDATE_RUN
```
