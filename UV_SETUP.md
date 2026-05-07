# UV Setup

This project now uses `uv` as the preferred environment and dependency manager.

## Prerequisites

- Python 3.12
- `uv`

## Recommended Commands

Create or refresh the virtual environment:

```powershell
uv venv --python 3.12
```

Install dependencies from `pyproject.toml`:

```powershell
uv sync
```

Run the main analysis flow:

```powershell
uv run python main.py
```

Generate test data:

```powershell
uv run python main.py --generate-test-data
```

Run chat mode:

```powershell
uv run python main.py --chat
```

Run multi-agent project summary:

```powershell
uv run python main.py --project-summary
```

Run multi-agent question answering:

```powershell
uv run python main.py --question "summarize current project capability"
```

Run the demo web app:

```powershell
uv run python demo_web.py
```

## Notes

- `pyproject.toml` is now the preferred source of truth for dependencies.
- `requirements.txt` can be kept temporarily for backward compatibility, but new dependency changes should be made in `pyproject.toml`.
- `.venv/` and `output/` are ignored in Git and should remain local to each machine.
