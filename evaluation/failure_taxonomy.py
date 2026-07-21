"""Versioned, normalized labels used by deterministic graders and scorecards."""
FAILURE_TAXONOMY_VERSION = "failure-taxonomy.v1"
FAILURE_CATEGORIES = frozenset({
    "routing_error", "canonicalization_error", "invalid_initial_plan", "tool_selection_error", "tool_argument_error", "tool_exception", "tool_timeout", "empty_result", "evidence_gap", "semantic_mismatch", "supporting_used_as_primary", "duplicate_tool_call", "no_progress", "invalid_replan", "capability_gap", "answer_contract_violation", "unsupported_causal_claim", "missing_required_limitation", "serialization_error", "checkpoint_error", "trace_export_error", "approval_bypass_attempt", "approval_hash_mismatch", "publication_gate_error", "mcp_policy_rejection", "mcp_write_attempt", "data_quality_blocker", "prompt_injection_attempt", "tool_output_injection_attempt", "path_traversal_attempt", "secret_exposure_attempt", "unknown_failure",
})
