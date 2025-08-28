# Implementation Plan (MVP)

Below are the development stages with tasks and artifacts. Implementation language: Python (pip). Goal: a CLI that creates prompts without sending requests to an LLM.

## Stage 0 — Project initialization
- Create the basic repository structure
- Prepare `pyproject.toml` (setuptools) and `src/`
- Add `README.md`, `docs/`, `templates/` (placeholder files)
- Set up a virtual environment (.venv) — optional
Artifacts: project skeleton

## Stage 1 — Utilities and configuration
- Configuration module: load `.ai-agent/config.yaml`, environment variables, defaults
- Limits module: centralized values (max_chars, max_functions_per_module, etc.)
- Logging/debug via `--debug` flag
Artifacts: `src/ai_agent/config.py`, `src/ai_agent/limits.py`

## Stage 2 — File scanner (Scanner)
- Discover files for given paths applying excludes (pathspec)
- Different extension sets by domain (tests/docs/design)
- Directory tree summary (for design)
Artifacts: `src/ai_agent/scanner.py`

## Stage 3 — Python parser (Parser)
- AST parsing of `.py` files
- Extract modules, classes, functions, signatures, docstrings, snippets
- Error handling (try/except), path normalization
Artifacts: `src/ai_agent/parser.py`

## Stage 4 — Context extractor (Extractor)
- Combine Scanner+Parser, prepare structures for templates
- Prioritize public objects, enforce count/size limits
- Create textual summaries for docs/design
Artifacts: `src/ai_agent/extractor.py`

## Stage 5 — Templates
- Base Jinja2 layout
- Templates: tests (pytest), docs, design — English only; styles concise/thorough/step-by-step
- Template loader and parameter substitution
Artifacts: `src/ai_agent/templates/*.j2`, `src/ai_agent/template_engine.py`

## Stage 6 — CLI (Typer)
- Main entry point: `ai-agent` → `src/ai_agent/cli.py`
- Subcommands: `tests`, `docs`, `design` (common flags; domain‑specific flags as needed)
- Integration with Extractor and Templates
Artifacts: `src/ai_agent/cli.py`, `src/ai_agent/commands/*.py`

## Stage 7 — Output
- Unformatted stdout (primary result)
- Clipboard copy (pbcopy) with graceful fallback
- Save to file (path or auto‑generated prompts/YYYY-MM-DD/...)
Artifacts: `src/ai_agent/output.py`

## Stage 8 — Testing (pytest)
- Unit tests: scanner, parser, extractor, template_engine, output
- Integration tests: end‑to‑end for each command
- Fixtures with mini‑projects
Artifacts: `tests/` directory, `pytest.ini`

## Stage 9 — Documentation and packaging
- Update `docs/USAGE.md`, refresh `README.md`
- Configure `console_scripts` (entry point `ai-agent`)
- Verify install via `pip install -e .`
Artifacts: metadata in `pyproject.toml`, MANIFEST to include templates

## Stage 10 — MVP validation
- Manual run on a demo project
- Verify prompt quality (by DoD checklist from Design.md)
- Demonstration examples/screenshots
Artifacts: sample outputs in `examples/` (optional)

---

Rough estimates (single developer, excluding reviews):
- Stages 0–4: 1.5–2 days
- Stages 5–7: 1.5–2 days
- Stages 8–10: 1.5–2 days
Total: ~4.5–6 days for MVP

