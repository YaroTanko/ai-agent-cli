# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository overview
- Purpose: Python 3.9+ CLI that generates high‑quality prompts for tests (pytest), documentation, and architecture/design.
- Entry point: console script `ai-agent` (defined in pyproject), implemented in `src/ai_agent/cli.py` (Typer).
- Key layers: CLI → Config → Scanner/Parser/Extractor → Template Engine (Jinja2) → Output (stdout/clipboard/file) → optional LLM (LangChain).
- Templates live in `templates/` (CWD preferred at runtime). Default config file: `.ai-agent/config.yaml`.
- Important docs: `README.md`, `docs/Design.md`, `docs/Implementation-Plan.md`, `docs/USAGE.md`.

Note: No existing WARP.md was found; this is the initial version.

## 1) Quickstart and common commands

Environment (macOS, zsh shown):

- Create and activate venv, install the package in editable mode
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
```

- CLI help and basic usage
```bash
ai-agent --help
# Generate a tests prompt from Python sources
ai-agent tests src/ --lang en --style thorough --out prompts/
# Generate a docs prompt from code + markdown
ai-agent docs README.md src/ --lang en --style step-by-step --out prompts/
# Generate a design/architecture prompt for the current repo
ai-agent design . --lang en --style concise --out prompts/
```

- Run with LM Studio (OpenAI‑compatible endpoint via LangChain)
```bash
# LM Studio server on http://localhost:1234/v1
export AI_AGENT_LLM_PROVIDER=lm-studio
export AI_AGENT_LLM_BASE_URL=http://localhost:1234/v1
export AI_AGENT_LLM_MODEL=openai/gpt-oss-20b   # or model you loaded
export AI_AGENT_LLM_API_KEY=lm-studio          # LM Studio accepts any non-empty value

# Send the rendered prompt to the model and print the answer
ai-agent tests src/ --run
ai-agent docs README.md src/ --run
ai-agent design . --run
```

- Building a distribution (optional)
```bash
python -m pip install -U build
python -m build
# artifacts in dist/
```

- Testing (pytest) — planned but not yet present in this repo
```bash
# once tests exist:
pip install pytest
pytest -q                          # run all tests
pytest tests/test_scanner.py::test_scan_paths -q   # run a single test
pytest -k "scanner and not slow" -q               # filter by expression
```

## 2) High‑level architecture (big picture)
- CLI (Typer) in `src/ai_agent/cli.py`
  - Subcommands: `tests`, `docs`, `design`.
  - Handles global options (`--config`, `--lang`, `--style`, `--max-chars`, `--debug`).
  - Orchestrates scan → parse → extract → render → output; `--run` triggers LLM call.
- Config in `src/ai_agent/config.py`
  - Precedence: defaults → explicit `--config` YAML → `.ai-agent/config.yaml` → environment variables (`AI_AGENT_*`).
  - LLM settings via `AI_AGENT_LLM_*` envs.
- Limits in `src/ai_agent/limits.py`
  - Centralized caps (characters, items per module, snippet lines, etc.).
- Scanner in `src/ai_agent/scanner.py`
  - Discovers files with `pathspec` excludes; `design` also summarizes a directory tree.
- Parser in `src/ai_agent/parser.py`
  - Python AST → ModuleInfo/ClassInfo/FunctionInfo; collects signatures, docstrings, short code snippets.
- Extractor in `src/ai_agent/extractor.py`
  - Builds project context, prioritizes public members, enforces limits, and produces module summaries for templates.
- Template engine in `src/ai_agent/template_engine.py`
  - Jinja2 templates loaded from `templates/` (prefers CWD/templates, then repo `templates/`).
  - Currently English templates only: `templates/tests/pytest_en.j2`, `templates/docs/docs_en.j2`, `templates/design/design_en.j2`.
- Output in `src/ai_agent/output.py`
  - Prints to stdout, optional clipboard copy (`pbcopy` on macOS), and optional file save when `--out` is used.
- LLM client in `src/ai_agent/llm.py`
  - Thin wrapper around `langchain-openai.ChatOpenAI`; supports providers: `lm-studio` and `openai`.

Data flow:
```
CLI → Config → Scanner → Parser → Extractor → TemplateEngine → Output → (optional) LLM
```

## 3) Practical notes and gotchas
- Console entry point: use `ai-agent` after `pip install -e .`. The `python -m ai_agent` module is a stub and does not expose the Typer CLI.
- Language/templates: the code supports a `--lang` option and config `lang`, but templates are English-only (`*_en.j2`). Setting `lang=ru` (default in `.ai-agent/config.yaml`) will not switch templates unless Russian templates are added.
- Style option: the engine enriches context with `style_text`, but current templates do not render this field explicitly (only the content style per template).
- Output saving: the command saves to a file only when `--out` is provided (either a file path or a directory). The “auto-generated path” behavior exists in `save_prompt()` but is currently gated by `--out` usage.
- Template discovery precedence: prefers `$(pwd)/templates/` during development; falls back to the repo’s `templates/` directory.
- Scanner excludes: controlled by config (`.ai-agent/config.yaml`) and `pathspec` patterns (e.g., `.git/**`, `.venv/**`, `__pycache__/**`, etc.). Matching is evaluated relative to `Path.cwd()`.
- LLM providers: implemented for `lm-studio` and `openai`. `ollama` is listed in config validation but not implemented yet.

## 4) Important project materials
- Quick intro and links: `README.md` (features, status, doc links)
- Design and big-picture decisions: `docs/Design.md`
- Implementation roadmap: `docs/Implementation-Plan.md`
- Usage expectations and env vars: `docs/USAGE.md`
- Repo defaults (including language, excludes, and LLM config): `.ai-agent/config.yaml`
