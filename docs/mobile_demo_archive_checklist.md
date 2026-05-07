# Mobile Demo Archive Checklist

## Goal

This checklist helps determine when `mobile-demo/` can be archived or deleted safely.

## Current Readiness Questions

### 1. Has `frontend/app/mobile` taken over the main mobile UI?

Check:

- mobile executive summary is shown in `frontend/app/mobile`
- KPI strip is shown in `frontend/app/mobile`
- chart area is shown in `frontend/app/mobile`
- AI chat drawer is shown in `frontend/app/mobile`

Current status:

- Yes, the main mobile executive demo is now served from `frontend/app/mobile`

### 2. Are shared proxy routes complete in `frontend/`?

Check:

- `GET /api/summary`
- `POST /api/ask`
- `GET /api/chart-catalog`
- `POST /api/chart`
- `POST /api/observe`
- `GET /api/observe-options`

Current status:

- Yes, the shared proxy layer already exists in `frontend/app/api/*`

### 3. Has chart rendering been consolidated?

Check:

- desktop uses shared chart implementation
- mobile uses shared chart implementation
- wrappers remain only for compatibility

Current status:

- Yes

### 4. Have chat utilities been consolidated?

Check:

- ask request builder is shared
- chart evidence extraction is shared
- assistant / user / error message shaping is shared
- quick prompts are grouped in shared constants

Current status:

- Yes

### 5. Have KPI / summary utilities been consolidated?

Check:

- KPI formatter logic is shared
- latest month / executive headline extraction is shared
- shared KPI card and snapshot item components exist

Current status:

- Yes

### 6. Does `mobile-demo/` still contain unique runtime behavior?

Review:

- unique mobile-only UI behavior not present in `frontend/app/mobile`
- unique API proxy routes not present in `frontend/app/api`
- unique chart / chat / KPI logic not already migrated

Current status:

- No known must-keep runtime behavior has been identified so far
- `mobile-demo/` still remains useful as a historical reference until one more cleanup and verification pass is complete

## Conditions For Archiving Or Deleting `mobile-demo/`

`mobile-demo/` can be considered ready for archival when all of the following are true:

- `/mobile` in `frontend/` fully covers the intended mobile demo
- no unique API proxy route remains only in `mobile-demo/`
- no unique chart, chat, or KPI logic remains only in `mobile-demo/`
- frontend build passes
- smoke checks pass for `/dashboard`, `/mobile`, `/api/summary`, `/api/ask`, `/api/chart`, and `/api/chart-catalog`
- the team agrees that `mobile-demo/` is no longer needed as a rollback reference

## Recommended Validation Before Deletion

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

## Recommendation

Current recommendation:

- `mobile-demo/` is archive-ready as a reference
- It is not deleted yet
- deletion requires final team approval
- if the team wants extra confidence, deletion should happen only after one more full manual demo verification
