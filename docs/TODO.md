# To‑Do (MVP)

Below is a detailed task list grouped by stages. Check items off as you complete them.

## Stage 0 — Project initialization
- [ ] Create repo structure: `src/`, `docs/`, `templates/`, `tests/`
- [ ] Add `pyproject.toml` (setuptools)
- [ ] Create a basic `README.md`
- [ ] (Opt.) Set up `.venv` and `requirements-dev.txt`

## Stage 1 — Configuration and limits
- [ ] Implement `src/ai_agent/config.py`
- [ ] Implement `src/ai_agent/limits.py`
- [ ] Support `.ai-agent/config.yaml`
- [ ] Support env vars: `AI_AGENT_LANG`, `AI_AGENT_STYLE`, `AI_AGENT_MAX_CHARS`

## Stage 2 — File scanner
- [ ] Implement `src/ai_agent/scanner.py` with pathspec excludes
- [ ] Support domain filters (tests/docs/design)
- [ ] Implement directory tree summary (for design)

## Stage 3 — Python parser (AST)
- [ ] Implement `src/ai_agent/parser.py`
- [ ] Extract functions/classes/docstrings/signatures
- [ ] Build snippets using lineno/end_lineno with limits
- [ ] Handle syntax and encoding errors

## Stage 4 — Context extractor
- [ ] Implement `src/ai_agent/extractor.py`
- [ ] Prioritize public objects, limit counts
- [ ] Create textual summaries for templates

## Stage 5 — Templates (Jinja2)
- [ ] Implement base template layout
- [ ] Create templates: `tests` (pytest) en
- [ ] Create templates: `docs` en
- [ ] Create templates: `design` en
- [ ] Implement loader and rendering in `template_engine.py`

## Stage 6 — CLI (Typer)
- [ ] `src/ai_agent/cli.py` — main entry
- [ ] `src/ai_agent/commands/tests.py`
- [ ] `src/ai_agent/commands/docs.py`
- [ ] `src/ai_agent/commands/design.py`
- [ ] Common flags: `--lang`, `--style`, `--copy`, `--out`, `--max-chars`, `--config`, `--debug`

## Stage 7 — Output
- [ ] `src/ai_agent/output.py` — stdout, pbcopy, file
- [ ] Error handling and fallback when pbcopy is unavailable
- [ ] Auto‑generate save path `prompts/YYYY-MM-DD/HHMMSS-<cmd>.txt`

## Stage 8 — Tests (pytest)
- [ ] Unit: scanner
- [ ] Unit: parser
- [ ] Unit: extractor
- [ ] Unit: template_engine
- [ ] Unit: output
- [ ] E2E: `ai-agent tests` on a mini‑project
- [ ] E2E: `ai-agent docs` on a mini‑project
- [ ] E2E: `ai-agent design` on a mini‑project

## Stage 9 — Documentation and packaging
- [ ] Update `docs/USAGE.md`
- [ ] Update `README.md`
- [ ] `pyproject.toml` — `console_scripts` for `ai-agent`
- [ ] MANIFEST to include templates/configs
- [ ] Verify `pip install -e .` in a clean environment

## Stage 10 — MVP validation
- [ ] Run on a demo project
- [ ] Check DoD compliance (Design.md)
- [ ] Screenshots/sample outputs in `examples/`

