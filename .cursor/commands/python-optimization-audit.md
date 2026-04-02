---
description: Python modernization audit — dependencies, idioms, structure, phased plan
---

# Python optimization / modernization audit

Run a **read-first audit** and produce a **phased plan**. Do **not** apply edits unless the user explicitly asks to implement after the plan.

## Scope (confirm or narrow)

- Default: this repository’s Python surface — `pyproject.toml`, `requirements*.txt`, `Pipfile*`, and `**/*.py` (prioritize `scripts/`, application packages).
- If the user gave paths, restrict the audit to those paths.

## 1) Dependency pass

- List direct dependencies and pins; note anything outdated or overly broad (`*` / unpinned prod).
- When helpful, suggest checks the user or agent can run if available (e.g. `pip index versions`, `pip-audit`, `uv pip`, PyPI) — do not assume a tool is installed.
- Flag **security/support** concerns (EOL Python, abandoned packages) briefly.
- Respect repo policy: single canonical `requirements.txt`, comment each new/changed dep (see `06-dependencies.mdc`).

## 2) Idiom pass

- Modern builtins and typing (`list[str]`, `dict[str, Any]`, `Path`, `match` only where it simplifies).
- Prefer `pathlib`, context managers, explicit encodings (UTF-8).
- Async only where the codebase already uses it or I/O-bound patterns clearly win.
- Note deprecated stdlib / patterns and migration cost.

## 3) Logic and structure pass

- Boundary vs core logic; duplication; overly large modules (see `03-code-structure.mdc`, `12-script-size-and-structure.mdc`).
- Error handling at **integration boundaries** only; align with `20-python-errors-and-observability.mdc`.

## 4) Output shape (required)

Produce:

1. **Executive summary** — top 5 wins vs effort.
2. **Phased plan** — phases with checkpoints, main risks, and how to validate each phase (tests, lint, smoke commands).
3. **What not to change** — align with `README.md` / `PLAN.md` if present; do not expand scope beyond the active phase without flagging it.
4. **Dependency table** (optional) — package, current pin, suggested action, note.

Ask whether to proceed with implementation only after the user confirms the plan.
