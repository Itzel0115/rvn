# Mobile Demo Archive Checklist

## Goal

This checklist records the final state of the former standalone mobile demo workspace.

## Final Status

The standalone `mobile-demo/` directory has been deleted. The mobile experience now lives in the unified frontend app:

```text
frontend/app/mobile
frontend/components/mobile
```

## Migration Checks

### 1. Has `frontend/app/mobile` taken over the main mobile UI?

Status: Yes.

The mobile executive summary, KPI strip, chart area, and AI chat drawer are served from `frontend/app/mobile`.

### 2. Are shared proxy routes complete in `frontend/`?

Status: Yes.

The shared proxy layer exists in `frontend/app/api/*` and covers:

- `GET /api/summary`
- `POST /api/ask`
- `GET /api/chart-catalog`
- `POST /api/chart`
- `POST /api/observe`
- `GET /api/observe-options`

### 3. Has chart rendering been consolidated?

Status: Yes.

Desktop and mobile use the shared chart implementation, with lightweight wrappers retained for import compatibility.

### 4. Have chat utilities been consolidated?

Status: Yes.

Ask request building, chart evidence extraction, message shaping, and quick prompts are shared.

### 5. Have KPI / summary utilities been consolidated?

Status: Yes.

KPI formatter logic, latest month / executive headline extraction, and shared KPI components live under `frontend/components/kpi`.

### 6. Does the deleted standalone workspace still contain unique runtime behavior?

Status: No known must-keep runtime behavior remains outside `frontend/`.

## Recommended Validation After Deletion

Run at minimum:

1. `npm run build` in `frontend/`
2. smoke check `/dashboard`
3. smoke check `/mobile`
4. smoke check `/api/summary`
5. smoke check `/api/ask`
6. smoke check `/api/chart`
7. smoke check `/api/chart-catalog`
8. verify KPI / summary display on both routes
9. verify chart rendering on both routes
10. verify ask flow still updates chart evidence on both routes
