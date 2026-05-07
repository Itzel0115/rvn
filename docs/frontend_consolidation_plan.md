# Frontend Consolidation Plan

## Purpose

This document tracks the consolidation of the separate desktop and mobile demo frontends into a single Next.js app under `frontend/`.

The original goals were:

- keep one primary Next.js app
- share API proxy routes
- share chart rendering logic
- share chat utilities
- share KPI / summary formatters and small components
- reduce duplicate maintenance cost before deciding whether `mobile-demo/` can be archived

## Current Status

The consolidation has now reached the point where the main user-facing routes live in `frontend/`:

- `/dashboard`
  Desktop analysis workspace
- `/mobile`
  Mobile executive demo

The following shared layers are already in place:

- shared chart rendering
- shared chat utilities and chart evidence adapter
- shared KPI / summary formatters and small presentational components

`mobile-demo/` is still present, but it is no longer the primary runtime path.

## Phase 5F Status

- `mobile-demo/` is now archived reference only
- `frontend/` is the primary runtime app
- future frontend work should target `frontend/`
- `mobile-demo/` is retained only for historical reference or rollback comparison until final team approval for deletion

## Current Structure

### Active app

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
  lib/
    python-api.js
```

### Reference app

```text
mobile-demo/
```

`mobile-demo/` remains as a reference copy while archive readiness is being reviewed.

## Shared Layers Completed

### Shared chart rendering

- Shared implementation:
  [frontend/components/charts/chart-surface.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/charts/chart-surface.jsx)
- Low-risk wrappers retained:
  - [frontend/components/chart-surface.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chart-surface.jsx)
  - [frontend/components/mobile/mobile-chart-surface.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/mobile/mobile-chart-surface.jsx)

### Shared chat utilities

- [frontend/components/chat/chat-utils.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chat/chat-utils.js)
- [frontend/components/chat/chart-evidence.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chat/chart-evidence.js)
- [frontend/components/chat/quick-prompts.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/chat/quick-prompts.js)

These now cover:

- ask request body construction
- assistant / user / error message shaping
- chart evidence extraction from `/api/ask`
- prompt grouping for analyst vs executive flows

### Shared KPI / summary utilities

- [frontend/components/kpi/kpi-utils.js](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/kpi/kpi-utils.js)
- [frontend/components/kpi/kpi-card.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/kpi/kpi-card.jsx)
- [frontend/components/kpi/snapshot-item.jsx](/C:/Users/itzel.hsiao/Desktop/revenue-poc/frontend/components/kpi/snapshot-item.jsx)

These now cover:

- latest month label extraction
- executive headline extraction
- KPI card data shaping
- snapshot item data shaping
- desktop vs mobile KPI display variants

## What Still Remains Before Archiving `mobile-demo/`

- frontend cleanup of legacy helpers and imports
- one more pass on low-risk dead-code removal in desktop/mobile console files
- confirm no unique mobile-only behavior still depends on `mobile-demo/`
- final archive readiness review

## Risks

- some desktop and mobile console files still contain older helper paths kept for low-risk migration
- removing wrappers too early could break imports
- `mobile-demo/` still contains historical build artifacts and old local runtime files, so deletion should only happen after a clean verification pass

## Validation Strategy

Before archiving `mobile-demo/`, the following should pass:

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

## Archive Readiness

See [mobile_demo_archive_checklist.md](/C:/Users/itzel.hsiao/Desktop/revenue-poc/docs/mobile_demo_archive_checklist.md) for the current archive checklist and exit criteria.
