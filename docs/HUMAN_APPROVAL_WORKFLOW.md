# Human Approval Workflow

Automatically allowed: scan metadata, quality checks, candidate creation, read-only investigation, draft generation, and pending approval creation.

Human approval required: local approved-artifact publication, replacement of any approved artifact, externally-ready status, and any future notification or write-back.

Permanently prohibited in this phase: auto/LLM approval, email, Slack, Teams, webhooks, source-data modification, database write-back, arbitrary paths, Python/SQL/shell execution, and MCP write tools.

Lifecycle: `pending → approved|rejected|revision_requested|cancelled`. Only a pending request can be decided. Approval requires `--approver`; rejection requires a reason; revision requires instructions. The request stores the draft content hash. A changed/superseded draft cannot be approved or published. Publication validates approval status, draft status, hash match, investigation status, and fixed output directory.


## Revision and identity closure

A revision request does not overwrite a draft. `create-revision` requires `revision_requested`, an explicit reviser identity, and instructions; it creates v2 and a new pending approval bound to the new hash. The old draft becomes superseded and the old request cannot approve or publish it. Caller identities are stored as unverified `cli_supplied`/`api_supplied` POC metadata, never as authenticated SSO/RBAC identities.
