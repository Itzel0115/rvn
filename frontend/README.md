# Frontend Workspace

`frontend/` is now the primary Next.js app for the project.

## Current Routes

- `/dashboard`
  Desktop analysis workspace. This route now owns the original desktop console experience.
- `/mobile`
  Mobile executive demo route. This route now owns the migrated mobile experience that originally lived in `mobile-demo/`.
- `/api/*`
  Shared Next.js proxy routes that forward requests to the Python API.

The root route `/` redirects to `/dashboard`.

## Shared Proxy Routes

The frontend app provides a single shared proxy layer:

- `GET /api/summary`
- `POST /api/ask`
- `GET /api/chart-catalog`
- `POST /api/chart`
- `POST /api/observe`
- `GET /api/observe-options`

The shared Python API client lives in [lib/python-api.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/lib/python-api.js).

## Shared Frontend Layers

The consolidation work completed so far has moved duplicated logic into shared frontend modules:

- Shared chart rendering
  - [components/charts/chart-surface.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/charts/chart-surface.jsx)
  - Desktop and mobile wrappers are still kept for low-risk imports:
    - [components/chart-surface.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chart-surface.jsx)
    - [components/mobile/mobile-chart-surface.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/mobile/mobile-chart-surface.jsx)
- Shared chat utilities and chart evidence adapter
  - [components/chat/chat-utils.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chat/chat-utils.js)
  - [components/chat/chart-evidence.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chat/chart-evidence.js)
  - [components/chat/quick-prompts.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chat/quick-prompts.js)
- Shared KPI / summary formatters and small components
  - [components/kpi/kpi-utils.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/kpi/kpi-utils.js)
  - [components/kpi/kpi-card.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/kpi/kpi-card.jsx)
  - [components/kpi/snapshot-item.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/kpi/snapshot-item.jsx)

## Development

1. Start the Python API:

```powershell
uv run python demo_web.py
```

2. Install frontend dependencies if needed:

```powershell
cd frontend
npm install
```

3. Start Next.js against the local Python API:

```powershell
$env:PYTHON_API_BASE="http://127.0.0.1:8765"
npm run dev
```

Production-like smoke checks can use:

```powershell
$env:PYTHON_API_BASE="http://127.0.0.1:8765"
npm run build
npm run start
```

## Current Status

- `/dashboard` is the stable desktop entry point
- `/mobile` is the stable mobile executive demo entry point
- Shared chart rendering is in place
- Shared chat utilities are in place
- Shared KPI / summary formatters and small presentational components are in place
- `mobile-demo/` is still retained as a reference workspace while archive readiness is being checked
- `mobile-demo/` is archived reference only and should not receive new feature work

## Transition Note

`mobile-demo/` has not been deleted yet. It is now in archive-readiness review rather than active feature ownership.

Before archiving or deleting `mobile-demo/`, we should confirm:

- `/mobile` fully covers the intended demo experience
- shared proxy routes remain stable
- chart, chat, and KPI behaviors are all validated in `frontend/`
- no remaining mobile-only functionality is still unique to `mobile-demo/`
