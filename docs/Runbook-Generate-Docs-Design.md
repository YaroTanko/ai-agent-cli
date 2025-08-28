# Runbook — Generate Docs and Design Prompts with ai-agent

Date: 2025-08-28
Environment: macOS (zsh), Python 3.12 in project-local venv
Project: /Users/yaroslavtanko/Developer/GenAI/ai-agent

## Goal
Verify docs and design prompt flows similar to tests: baseline to stdout, save to file with clipboard, and env override demonstrating truncation.

## Setup
Assumes venv is already created and package installed (see Runbook-Generate-Tests.md).

## Docs flows

1) Baseline to stdout
```bash
./.venv/bin/ai-agent --lang en --style thorough docs README.md src/
```
Observations: Printed materials summary (modules + other files) and requirements; no errors.

2) Save to file and copy to clipboard
```bash
./.venv/bin/ai-agent --lang en --style thorough docs README.md src/ --out prompts/ --copy
```
Artifacts: `prompts/prompt-docs.txt` created; clipboard copy succeeded (no pbcopy warning).

3) Env override for truncation
```bash
AI_AGENT_MAX_CHARS=1000 \
./.venv/bin/ai-agent --lang en --style thorough docs README.md src/ \
  --out prompts/prompt-docs-truncated.txt
```
Artifacts: `prompts/prompt-docs-truncated.txt` (~1KB) with a "... (truncated)" marker.

## Design flows

1) Baseline to stdout
```bash
./.venv/bin/ai-agent --lang en --style concise design .
```
Observations: Printed directory tree and key components summary; no errors.

2) Save to file and copy to clipboard
```bash
./.venv/bin/ai-agent --lang en --style concise design . \
  --out prompts/prompt-design-2.txt --copy
```
Artifacts: `prompts/prompt-design-2.txt` created; clipboard copy succeeded.

3) Env override for truncation
```bash
AI_AGENT_MAX_CHARS=1000 \
./.venv/bin/ai-agent --lang en --style concise design . \
  --out prompts/prompt-design-truncated.txt
```
Artifacts: `prompts/prompt-design-truncated.txt` (~1.3KB) with truncation.

## Notes and gotchas
- Global options must be placed before the subcommand (Typer):
  - Correct: `ai-agent --lang en --style thorough docs README.md src/`
- When passing a directory to `--out`, the CLI writes default filenames: `prompt-docs.txt` or `prompt-design.txt`. To avoid overwriting an existing design prompt, you can pass an explicit file path (e.g., `--out prompts/prompt-design-2.txt`).
- Templates are English-only; prefer `--lang en`.
- Env var precedence follows config loader rules: defaults -> explicit `--config` -> `.ai-agent/config.yaml` -> environment variables.

