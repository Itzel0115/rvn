# Demo Checklist

## Start Backend

```powershell
.\.venv\Scripts\python.exe demo_web.py
```

Expected backend URL:

```text
http://127.0.0.1:8765
```

## Start Frontend

Desktop dashboard:

```powershell
cd frontend
$env:PYTHON_API_BASE = "http://127.0.0.1:8765"
npm run dev
```

Open:

```text
http://127.0.0.1:3000/dashboard
```

Mobile route:

```text
http://127.0.0.1:3000/mobile
```

If port 3000 is occupied, use another port:

```powershell
npm run dev -- -p 3001
```

## Required Demo Questions

- 請分析哪個平台表現較佳
- 請分析哪個平台表現較差
- 比較 8 月各平台營收與庫存
- 哪個平台最健康？
- 最近有什麼營運風險？
- 8 月相較 7 月營收變化主要由誰貢獻？
- 資料涵蓋哪些月份？
- 下個月營收會不會改善？

## Expected Behavior

- Executive answer should show `display_blocks.headline` first.
- Key observations should come from `display_blocks.key_observations`.
- Key observations should be no more than `answer_plan.max_key_observations`.
- Raw `domainResults.key_findings` should not appear in the main executive highlights when display blocks exist.
- `domainResults` can remain available in collapsed debug details.
- Platform performance questions should use `get_platform_performance_snapshot`.
- Best/healthy platform questions should mention `health_score`.
- Weak/attention platform questions should not use inventory amount ranking alone.
- Same-month platform comparison should not be answered as MoM contribution.
- Forecast questions should be rejected or limited, not predicted.
- Diagnosis questions should not claim root cause is confirmed.

## LLM Settings

Keep both settings off by default for demos:

- `use_llm_planner=false`
- `use_llm_rewriter=false`

The deterministic tools, rubric registry, evidence projector, and answer contract remain the source of truth.

## Automated Smoke

Direct deterministic smoke:

```powershell
.\.venv\Scripts\python.exe scripts\demo_smoke.py
```

API smoke against a running backend:

```powershell
.\.venv\Scripts\python.exe scripts\demo_smoke.py --api-url http://127.0.0.1:8765
```

Outputs:

- `eval/demo_smoke_report.md`
- `eval/demo_smoke_results.csv`

## Common Troubleshooting

- If frontend `/api/*` calls fail, confirm `PYTHON_API_BASE` points to `http://127.0.0.1:8765`.
- If Chinese questions appear as `????` in logs, rerun from a UTF-8 capable terminal or use the UI input box.
- If `npm run build` fails with `spawn EPERM`, rerun build from an unrestricted shell because Next.js needs worker subprocesses.
- If a performance answer falls back to insufficient evidence, verify `get_platform_performance_snapshot` appears in `tools_used`.
- If key observations look noisy, inspect `answer_contract.role_based_evidence` and confirm background/debug items are not projected.
