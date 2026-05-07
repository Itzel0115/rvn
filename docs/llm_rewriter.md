# Phase 7B LLM Rewriter

## Goal

Phase 7B adds an experimental LLM answer rewriter with strict guardrails.

The rewriter may only improve:

- tone
- paragraph flow
- readability

The rewriter may not:

- add new facts
- add new numbers
- add new conclusions
- claim root cause
- forecast future performance

The deterministic `answer_contract` remains the only source of truth.

## Scope

The rewriter only operates on `answer_contract.answer`.

It does not modify:

- `evidence`
- `tools_used`
- `data_scope`
- `limitations`
- `suggested_followups`

If rewriting succeeds and passes validation, only the `answer` field is replaced.

## Rewrite Schema

The rewriter request includes:

- `question`
- `deterministic_answer`
- `answer_contract`
- `evidence`
- `limitations`
- `tools_used`

The LLM must return JSON:

```json
{
  "rewritten_answer": "..."
}
```

## Validator Rules

The validator is deterministic and enforces:

1. Number safety
   The rewritten answer cannot introduce numbers that do not already appear in the deterministic answer or evidence.

2. Forbidden phrases
   Rewrites are rejected if they contain phrases such as:
   - `原因就是`
   - `一定是`
   - `已確認根本原因`
   - `預測會`
   - `下個月一定`
   - `導致`
   - `confirmed root cause`
   - `will improve`
   - `will decline`

3. Limitation preservation
   If the original answer or limitations contain reasoning constraints, missing data constraints, or proxy constraints, the rewritten answer must preserve equivalent limitation semantics.

4. Length control
   The rewritten answer cannot exceed 2.5x the deterministic answer length.

## Fallback Strategy

The rewriter is optional and off by default.

It can be enabled through:

- `MultiAgentAssistant(..., use_llm_rewriter=True)`
- environment variable `USE_LLM_REWRITER=true`

Fallback happens when:

- the LLM call fails
- the JSON output is invalid
- `rewritten_answer` is empty
- validator rules fail

When fallback happens, the system keeps the original deterministic answer unchanged.

## Why The LLM Still Does Not Answer Freely

This phase intentionally keeps the deterministic answer as the stable source of truth because:

- evidence grounding must remain auditable
- safety rules must stay deterministic
- answer wording can improve without changing the `/api/ask` response contract
- planning, analysis, and wording can be evolved independently

## Live Smoke Test

Phase 7C also uses the live smoke script:

- [scripts/smoke_llm_live.py](/C:/Users/itzel.hsiao/Desktop/revenue-poc/scripts/smoke_llm_live.py)

The script checks:

- planner success or fallback
- deterministic answer generation
- rewrite success or fallback
- validation failures such as new numbers, forbidden phrases, or missing limitation semantics

How to run:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py
```

Default behavior:

- without `--live`, the script only writes an availability / skip report
- this keeps local verification safe when the configured live model is not responsive
- use `--live` only when you explicitly want to measure real rewrite fallback and validator behavior

Timeout behavior:

- the live smoke script now uses `--timeout-seconds`, with a default of at least `120`
- rewriter transport failures are classified separately from validator failures
- a timeout is reported as `llm_timeout`, not as `rewriter_validation_failed`

If a live model is reachable:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py --live
```

Planner-only live smoke:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py --live --planner-only --timeout-seconds 30 --warmup
```

If no live LLM is available, the script writes an `unavailable` report instead of crashing.

Warmup behavior:

- `--warmup` runs a single JSON probe before the case loop
- if warmup fails, the report records `warmup_failed`
- warmup failure prevents the live smoke loop from running, which keeps the diagnostic output easier to interpret

## How To Read Rewrite Fallback

- rewrite fallback is expected during experimentation
- validation failure is a safety success if it prevents unsupported wording from replacing the deterministic answer
- a successful rewrite is only acceptable when the rewritten answer stays fully grounded in the original deterministic content

## How To Read Timeout vs Validation Failure

- `llm_timeout` means the model never returned a usable response within the configured timeout
- `invalid_json` means the model returned text that could not be parsed as the required JSON
- `rewriter_validation_failed` means the validator examined the rewritten text and rejected it
- `forbidden_phrase_violation`, `new_number_violation`, and `limitation_violation` are safety-specific validator outcomes

## Why Live Rewrite Does Not Mean We Should Turn It On By Default

Even if live rewrite looks fluent:

- deterministic answer text remains the safe baseline
- validator coverage is still heuristic, not a full proof system
- rollout decisions should depend on repeated live smoke runs and curated business-question review
