# Runbook — Generate Test Prompts with ai-agent (tests subcommand)

Date: 2025-08-28
Environment: macOS (zsh), Python 3.12 in project-local venv
Project: /Users/yaroslavtanko/Developer/GenAI/ai-agent

## Goal
Generate test prompts using the ai-agent CLI `tests` subcommand, validate stdout output, saving to file, clipboard copy, and environment/config overrides. Optional LLM execution was skipped because LM Studio was not detected locally.

## Setup

```bash
# Create venv and install the project in editable mode
python3 -m venv .venv
./.venv/bin/python -m pip install -U pip
./.venv/bin/pip install -e .

# Verify CLI is available
./.venv/bin/ai-agent --help
```

Notes:
- The CLI provides global options on the root command (e.g., `--lang`, `--style`, `--max-chars`). Place them before the subcommand (e.g., `ai-agent --lang en tests ...`).

## Runs

1) Baseline tests prompt to stdout

```bash
./.venv/bin/ai-agent --lang en --style thorough tests src/
```

Result: Printed a prompt with a summary like `modules=11, functions=31, classes=11` and a modules/functions overview. No errors observed.

2) Save prompt to file and copy to clipboard

```bash
mkdir -p prompts
./.venv/bin/ai-agent --lang en --style thorough tests src/ --out prompts/ --copy
```

Results:
- File saved: `prompts/prompt-tests.txt`
- Clipboard: copied successfully on macOS (no warnings printed)

3) Include private members

```bash
./.venv/bin/ai-agent --lang en --style thorough tests src/ \
  --include-private --out prompts/prompt-tests-private.txt
```

Result: Saved to `prompts/prompt-tests-private.txt`. Output includes private (`_`-prefixed) functions/methods.

4) Environment override for max functions per module

```bash
AI_AGENT_MAX_FUNCS_PER_MODULE=50 \
./.venv/bin/ai-agent --lang en --style thorough tests src/ \
  --out prompts/prompt-tests-fpm50.txt
```

Result: Saved to `prompts/prompt-tests-fpm50.txt`. In this repository, modules don’t exceed the default, so visible differences may be small; the override is in effect for larger modules.

5) Optional LLM execution (skipped)

```bash
# Detect LM Studio
curl -sS -m 2 http://localhost:1234/v1/models
# -> Connection failed; LM Studio not detected, so skipping --run
```

If LM Studio is running, you can test:

```bash
AI_AGENT_LLM_PROVIDER=lm-studio \
AI_AGENT_LLM_BASE_URL=http://localhost:1234/v1 \
AI_AGENT_LLM_MODEL=openai/gpt-oss-20b \
AI_AGENT_LLM_API_KEY=lm-studio \
./.venv/bin/ai-agent --lang en --style thorough tests src/ --run --out prompts/prompt-tests-llm.txt
```

## Artifacts

As of this run:

```text
$ ls -l prompts
prompt-design.txt               # from prior run (kept)
prompt-tests.txt                # baseline saved
prompt-tests-private.txt        # with private members included
prompt-tests-fpm50.txt          # with env override for functions per module
```

## Gotchas and notes
- Global options must precede the subcommand. Example: `ai-agent --lang en --style thorough tests src/`.
- `--out` behavior:
  - If you pass a directory (e.g., `prompts/`), ensure it exists before running so the CLI recognizes it as a directory and appends `prompt-tests.txt`.
  - You can pass an explicit file path to `--out` to avoid ambiguity (e.g., `--out prompts/prompt-tests-private.txt`).
- Templates are English-only; set `--lang en` (the repository’s default `.ai-agent/config.yaml` sets `lang: ru`, but CLI args override it).
- Clipboard copy uses `pbcopy` on macOS. If unavailable, the CLI prints a warning and continues.
- Environment/config precedence: defaults -> explicit `--config` YAML (if supplied) -> `.ai-agent/config.yaml` -> environment variables (e.g., `AI_AGENT_MAX_FUNCS_PER_MODULE`).

