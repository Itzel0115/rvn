# LLM Enablement Runbook

## Current Default

LLM planner and rewriter are off by default.

- `USE_LLM_PLANNER=false`
- `USE_LLM_REWRITER=false`

Do not commit or deploy a change that turns either feature on by default unless there is an explicit rollout decision.

## Ollama Startup

Start Ollama locally before live smoke:

```powershell
ollama serve
```

If Ollama is already running as a service, this command may report that the port is in use. In that case, continue with the checks below.

## Confirm Ollama Is Reachable

Check the local tags endpoint:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

Or use the Ollama CLI:

```powershell
ollama list
```

Confirm that the configured model is present. The current default is:

```powershell
$env:OLLAMA_MODEL="gemma4:e4b"
```

If the model is missing, pull it explicitly:

```powershell
ollama pull gemma4:e4b
```

## Runtime Settings

The project reads these Ollama settings from environment variables, with safe defaults in `config.py`:

```powershell
$env:OLLAMA_BASE_URL="http://localhost:11434"
$env:OLLAMA_MODEL="gemma4:e4b"
$env:OLLAMA_TIMEOUT_SECONDS="90"
```

For Phase 10A planner-only product testing:

```powershell
$env:USE_LLM_PLANNER="true"
$env:USE_LLM_REWRITER="false"
```

For isolated rewriter smoke only, use the live smoke script rather than turning rewrite on for the app by default.

## Smoke Commands

Availability-only smoke, no live model loop:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py
```

Planner-only live smoke:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py --live --planner-only --timeout-seconds 60 --warmup
```

Planner plus rewriter live smoke, for validation only:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_llm_live.py --live --timeout-seconds 90 --warmup
```

Deterministic regression checks should still be run after any live LLM smoke:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\demo_answer_review.py
```

## Fallback Behavior

Planner fallback keeps deterministic routing and answer generation.

Fallback is expected when:

- Ollama is unreachable
- the model times out
- the model returns invalid JSON
- the planner proposes an unknown tool
- the planner proposes invalid args, metrics, or dimensions
- forecast safety or why/cause limitation rules fail

Rewriter fallback keeps the original deterministic `answer_contract.answer`.

Fallback is expected when:

- Ollama is unreachable
- the model times out
- the model returns invalid JSON
- the rewrite introduces new numbers
- the rewrite drops required limitations
- the rewrite claims root cause or forecast

## API Contract

Enabling planner or rewriter must not remove or rename existing `/api/ask` fields.

Planner output is internal routing metadata. The final answer still comes from deterministic tools and `answer_contract.py`.

Rewriter may only replace `answer_contract.answer` after validation. It must not change:

- `evidence`
- `tools_used`
- `data_scope`
- `limitations`
- `suggested_followups`
- `display_blocks`

## Demo Recommendation

For executive demo readiness, keep the deterministic path as the default.

Recommended demo setting:

```powershell
$env:USE_LLM_PLANNER="false"
$env:USE_LLM_REWRITER="false"
```

Planner can be enabled in a rehearsal only after live smoke shows acceptable planner success/fallback behavior:

```powershell
$env:USE_LLM_PLANNER="true"
$env:USE_LLM_REWRITER="false"
```

Do not officially enable the rewriter for demo unless its live smoke passes repeatedly and the rewritten answers are manually reviewed.
