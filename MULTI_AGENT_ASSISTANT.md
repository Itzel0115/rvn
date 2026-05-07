# Multi-Agent Assistant Guide

## Overview

This project now includes a runnable multi-agent analysis assistant built on top of the existing data pipeline.

The design keeps the current Excel-based workflow and analysis modules, then adds:

- a shared Ollama client
- a main orchestration agent
- domain agents
- a tool layer that reuses existing analysis outputs
- structured logging with `request_id`

All agents are configured to use Ollama model `gemma:e4b`.

## Project-Fit Design

The assistant does **not** replace the original reporting pipeline.

It reuses:

- `data_loader.py`
- `mapping_parser.py`
- `analyzer.py`
- existing cleaned / summary / merged analysis outputs

The new layer only adds orchestration and tool-oriented access on top of the current project.

## Added / Updated Files

- `ollama_client.py`
  Shared Ollama wrapper for `gemma:e4b`, prompt handling, JSON parsing, exception handling, and logging.
- `analysis_pipeline.py`
  Wraps the existing load / parse / analyze flow into a reusable pipeline context.
- `analysis_tools.py`
  Exposes reusable tool methods for trends, rankings, anomalies, correlations, and platform ratios.
- `multi_agent.py`
  Implements the main agent plus `sales`, `inventory`, `financial`, and `association` domain agents.
- `logging_utils.py`
  Shared logging configuration with console + file logging and `request_id`.
- `main.py`
  Supports agent mode through `--agent-question`, `--question`, `--agent-project-summary`, and `--project-summary`.
- `llm_reporter.py`
  Reworked to use the same shared Ollama client.

## Agent Responsibilities

### Main Agent

The main agent is implemented in `multi_agent.py` and is responsible for:

- question understanding
- question classification
- task decomposition
- routing to domain agents
- collecting child-agent outputs
- synthesizing a final answer

If Ollama is unavailable, it falls back to deterministic routing so the assistant remains usable.

### Sales Agent

Focus:

- revenue trend
- revenue ranking
- scoped revenue analysis by month / platform / business group

Tools:

- `get_metric_table("revenue_trend", filters)`
- `get_top_groups("revenue", filters)`

### Inventory Agent

Focus:

- inventory amount trend
- inventory QTY trend
- scoped inventory analysis by month / platform / business group

Tools:

- `get_metric_table("inventory_amount_trend", filters)`
- `get_metric_table("inventory_qty_trend", filters)`
- `get_top_groups("inventory", filters)`

### Financial Agent

Focus:

- revenue / inventory proxy ratios
- anomaly interpretation
- partial financial diagnostics

Tools:

- `get_platform_ratios(filters)`
- `get_anomalies(filters)`

Note:

This project does not currently contain full financial statement fields, so this agent returns `partial` when asked about margin, expense, cashflow, or similar topics.

### Association Agent

Focus:

- correlation analysis
- association fallback explanation

Tools:

- `get_correlations()`

Note:

The current data is not transaction-level, so true association rules / basket analysis are not directly supported.

## Actual Data Observed

### `data/inventory.xlsx`

- `日期`
- `HQBU`
- `金額`
- `QTY`
- `新事業群`

### `data/revenue.xlsx`

- `日期`
- `平台`
- `營收`
- `新事業群`

### `data/mapping.xlsx`

- `事業群名稱`
- `事業群代碼`
- `庫存HQBU分類名稱`
- `庫存HQBU代碼`
- `金額處理方式`
- `QTY處理方式`
- `營收平台分類名稱`
- `營收平台代碼`
- `實際營收處理方式`

## Supported Question Types

- revenue trend questions
- inventory trend questions
- group ranking questions
- scoped questions by month / business group / platform
- cross-domain diagnosis questions
- anomaly summary questions
- correlation / fallback association questions
- project capability summary questions

## Current Limits

- no transaction-level basket data
- no full finance statement schema
- product / SKU level analysis is not available in the current source files
- if local Ollama endpoint is unavailable, the system uses deterministic fallback

## Run

### Existing analysis pipeline

```bash
python main.py
```

### Multi-agent project summary

```bash
python main.py --agent-project-summary
python main.py --project-summary
```

### Multi-agent question answering

```bash
python main.py --agent-question "請分析最新營收與庫存趨勢"
python main.py --question "新事業群 2 的營收趨勢如何？"
python main.py --question "為什麼某產品賣得好但庫存還偏高？"
python main.py --question "目前能不能做 association rules？如果不行，請給我 fallback 分析"
```

### JSON output

```bash
python main.py --question "請分析最新營收與庫存趨勢" --agent-json
```

### Debug logging

```bash
python main.py --question "請分析最新營收與庫存趨勢" --agent-debug

### Frontend demo

```bash
python demo_web.py
```

Then open:

```text
http://127.0.0.1:8765
```

The frontend demo is a presentation UI that:

- shows the agent library and supported domains
- lets you submit a question from the browser
- calls the same `MultiAgentAssistant`
- displays request id, routing, subtasks, and child-agent outputs
```

## Logging

### Logger setup

- shared setup: `logging_utils.py`
- log file: `output/logs/multi_agent_assistant.log`

### Log fields

Each line includes:

- timestamp
- log level
- logger name
- `request_id`
- `domain`
- message

### What gets logged

- pipeline file loading
- actual source file paths
- row counts
- mapping parsing results
- main-agent classification and routing
- task decomposition
- child-agent dispatch
- tool execution start / end
- fallback / warning / unsupported cases
- LLM call failures

### How to trace one run

1. run a question once
2. note the `Request ID` printed in the answer
3. search that ID in `output/logs/multi_agent_assistant.log`

## Ollama Notes

The assistant is configured to call:

- model: `gemma:e4b`
- endpoint: `http://localhost:11434/api/generate`

If your environment returns `404` or another connection error, the assistant will still run using deterministic fallback logic.

To use live Ollama generation, make sure:

- Ollama is installed and running
- the endpoint is reachable
- model `gemma:e4b` is available locally

## Example Prompts

- `請幫我總結目前資料可支援哪些分析`
- `新事業群 2 的營收趨勢如何？`
- `雲端服務的營收趨勢如何？`
- `GG-04 平台的營收趨勢如何？`
- `2024-08 的營收是多少？`
- `為什麼某產品賣得好但庫存還偏高？`
- `目前能不能做 association rules？如果不行，請給我 fallback 分析`
