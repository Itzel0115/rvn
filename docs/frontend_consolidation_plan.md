# Frontend Consolidation Plan

## Purpose

This document records the consolidation of the former separate desktop and mobile demo frontends into a single Next.js app under `frontend/`.

The goals were:

- keep one primary Next.js app
- share API proxy routes
- share chart rendering logic
- share chat utilities
- share KPI / summary formatters and small components
- remove the standalone mobile workspace after migration

## Current Status

The consolidation is complete at the workspace level. The main user-facing routes now live in `frontend/`:

- `/dashboard`
  Desktop analysis workspace.
- `/mobile`
  Mobile executive demo.

The following shared layers are in place:

- shared chart rendering
- shared chat utilities and chart evidence adapter
- shared KPI / summary formatters and small presentational components
- shared Next.js API proxy routes

The former standalone `mobile-demo/` directory has been deleted. Future desktop and mobile frontend work should target `frontend/`.

## Current Structure

```text
frontend/
  app/
    dashboard/
    mobile/
    api/
  components/
    charts/
    chat/
    kpi/
    mobile/
  lib/
    python-api.js
```

## Shared Layers Completed

### Shared chart rendering

- Shared implementation: `frontend/components/charts/chart-surface.jsx`
- Compatibility wrappers retained:
  - `frontend/components/chart-surface.jsx`
  - `frontend/components/mobile/mobile-chart-surface.jsx`

### Shared chat utilities

- `frontend/components/chat/chat-utils.js`
- `frontend/components/chat/chart-evidence.js`
- `frontend/components/chat/quick-prompts.js`

These cover:

- ask request body construction
- assistant / user / error message shaping
- chart evidence extraction from `/api/ask`
- prompt grouping for analyst vs executive flows

### Shared KPI / summary utilities

- `frontend/components/kpi/kpi-utils.js`
- `frontend/components/kpi/kpi-card.jsx`
- `frontend/components/kpi/snapshot-item.jsx`

These cover:

- latest month label extraction
- executive headline extraction
- KPI card data shaping
- snapshot item data shaping
- desktop vs mobile KPI display variants

## Validation Strategy

After the deletion, validation should focus on the unified `frontend/` app:

- `/dashboard` loads successfully
- `/mobile` loads successfully
- `/api/summary` works
- `/api/ask` works
- `/api/chart` works
- `/api/chart-catalog` works
- KPI / summary sections render correctly
- chart rendering works on both desktop and mobile
- chat flow still updates chart state after chart evidence is returned
- `npm run build` succeeds in `frontend/`
