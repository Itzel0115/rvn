# Revenue Intelligence POC Handoff Site

This static site is served by the existing Next.js frontend from `frontend/public/handoff/`.

- Formal entry: `/handoff/`
- Direct entry: `/handoff/index.html`
- Generated source: `scripts/generate_handoff_site.py`
- Validator: `scripts/validate_handoff_site.py`
- Tool catalog count: 30
- MCP catalog count: 6

Regenerate after tool registry, semantic definitions, evaluation datasets, or core startup docs change:

```bash
uv run python scripts/generate_handoff_site.py
uv run python scripts/validate_handoff_site.py
```
