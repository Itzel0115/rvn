# Frontend Workspace

`frontend/` is the single active Next.js app for the project.

## Current Routes

- `/dashboard`
  Desktop analysis workspace.
- `/mobile`
  Mobile executive demo route. This route owns the mobile experience that was migrated out of the former standalone mobile app.
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

The shared Python API client lives in `frontend/lib/python-api.js`.

## Shared Frontend Layers

The consolidation work moved duplicated logic into shared frontend modules:

- Shared chart rendering
  - `frontend/components/charts/chart-surface.jsx`
  - Compatibility wrappers:
    - `frontend/components/chart-surface.jsx`
    - `frontend/components/mobile/mobile-chart-surface.jsx`
- Shared chat utilities and chart evidence adapter
  - `frontend/components/chat/chat-utils.js`
  - `frontend/components/chat/chart-evidence.js`
  - `frontend/components/chat/quick-prompts.js`
- Shared KPI / summary formatters and small components
  - `frontend/components/kpi/kpi-utils.js`
  - `frontend/components/kpi/kpi-card.jsx`
  - `frontend/components/kpi/snapshot-item.jsx`

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

Then open:

- Desktop: `http://127.0.0.1:3000/dashboard`
- Mobile: `http://127.0.0.1:3000/mobile`

Production-like smoke checks can use:

```powershell
$env:PYTHON_API_BASE="http://127.0.0.1:8765"
npm run build
npm run start
```

## Current Status

- `/dashboard` is the stable desktop entry point.
- `/mobile` is the stable mobile executive demo entry point.
- Shared API proxy routes are in `frontend/app/api/*`.
- Shared chart rendering is in place.
- Shared chat utilities are in place.
- Shared KPI / summary formatters and small presentational components are in place.
- The former standalone `mobile-demo/` workspace has been deleted after migration into `frontend/`.
