# Mobile Demo Archive Notice

`mobile-demo/` is now an archived reference only.

## Status

- Active shared frontend app: `frontend/`
- Active desktop route: `frontend/app/dashboard`
- Active mobile route: `frontend/app/mobile`
- Shared proxy routes: `frontend/app/api/*`

## What This Directory Is For

Use `mobile-demo/` only as:

- a historical reference for the original standalone mobile demo
- a rollback reference if the team needs to compare an older implementation

## What Not To Do

Do not:

- add new features here
- treat this directory as an active runtime path
- update API proxy behavior here
- continue new frontend development here

All future frontend work should happen in `frontend/`.

## Current Migration Outcome

The mobile executive demo experience has already been moved into the shared frontend app:

- mobile UI now lives in `frontend/app/mobile`
- desktop UI now lives in `frontend/app/dashboard`
- chart rendering is shared in `frontend/components/charts/`
- chat utilities are shared in `frontend/components/chat/`
- KPI / summary utilities are shared in `frontend/components/kpi/`

## Deletion Policy

This directory is not deleted yet.

It should remain available as an archived reference until the team explicitly approves final removal after one more full manual demo verification, if needed.
