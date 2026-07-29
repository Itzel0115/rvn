# Revenue & Inventory Agentic Analysis POC

## Project Overview

A local Agentic AI proof-of-concept for deterministic revenue and inventory analysis. Python normalizes and aligns Excel data, analysis tools calculate evidence, and Agents plan questions and present validated results through API, CLI, and web UI. The system does not modify source Excel files or train models.

## Current Data Sources

The only formal sources are:

- `data/inventory.xlsx`
- `data/revenue.xlsx`

`mapping.xlsx` and its fallback are removed. Any remaining `ParsedMapping` object is internal compatibility metadata derived from inventory/revenue data, not a third input file.

## Architecture

- `demo_web.py` — Python API, normally on `http://127.0.0.1:8765`
- `analysis_pipeline.py` — builds the pipeline context
- `real_data.py` — normalization, validation, and entity/month alignment
- `multi_agent.py` — Agent orchestration
- `analysis_tools.py` — deterministic analysis tools
- `tool_registry.py` — tool contracts and registration
- `agent_cli.py` — Agent/project-summary CLI
- `frontend/` — Next.js dashboard and mobile UI

## Quick Start

Prerequisites: Python 3.12, `uv`, and Node.js/npm for the frontend.

```bash
uv sync
uv run python main.py --project-summary
```

Start the backend from the repository root:

```bash
uv run python demo_web.py
```

In another terminal, install and start the frontend:

```bash
cd frontend
npm install
PYTHON_API_BASE=http://127.0.0.1:8765 npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open `/dashboard` or `/mobile` at `http://127.0.0.1:3000`. Windows startup scripts are under `scripts/`.

## Smoke Tests

```bash
uv run pytest -q tests/test_real_data_contract.py tests/test_data_loader.py tests/test_status_apis.py tests/test_mcp_tools.py
uv run python -m py_compile analysis_pipeline.py real_data.py demo_web.py agent_cli.py
```

With the backend running, check `GET /api/health` and `GET /api/summary`. For a frontend production-like check, run `npm run build` and then `npm run start` in `frontend/`.

## Handoff Documentation

Handoff site path: served by the existing Next.js frontend at `/handoff/` or `/handoff/index.html`.

## Known Limitations

- The data supports descriptive analysis and proxy efficiency signals, not causal conclusions.
- Forecasting and transaction-level basket analysis are not supported.
- Missing fields, invalid dates, numeric parse errors, and one-sided source rows are data-quality limitations.
- The API and frontend are local development/demo services, not a production deployment.
- Compatibility names such as `ParsedMapping`, `AnalysisArtifacts`, and `get_mapping_summary()` remain for existing Agent/tool consumers.
