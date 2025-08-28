# AI-Agent CLI — System Design (MVP)

Status: MVP project (Python CLI, package manager: pip). Primary flow: prompt generation and printing. Optional: direct LLM calls via LangChain to an OpenAI‑compatible endpoint (LM Studio preferred).


## 1. Goals and context

- Goal: provide a CLI tool that produces high‑quality prompts for:
  1) writing tests (pytest, Python),
  2) documentation (technical/user),
  3) architecture/design prompts.
- Context source: the user’s local project. The tool extracts code/file structure, docstrings, signatures, and short snippets.
- Output: a ready prompt printed to stdout with options to copy to clipboard (macOS pbcopy) and/or save to a file.
- MVP constraints:
  - No remote API calls, does not send requests to LM Studio.
  - Focus on Python code for pytest prompt generation and generic templates for docs/design.


## 2. Scope and non‑goals

Included in MVP:
- Commands: tests, docs, design.
- Extract context from user‑provided local files/directories.
- Template‑based prompt generation (Jinja2) with English language and style (concise/thorough/step‑by‑step) selection.
- Content size limiting (trimming, prioritizing relevant parts).
- View result in terminal, options to copy and save to a file.

Not included in MVP:
- Iterative agentic loops with memory/tools; only single prompt execution via `--run`.
- Languages other than Python for the tests command.
- Advanced static analysis (full‑project typing, call graph); only lightweight AST heuristics.


## 3. User scenarios (US)

- US1 (tests): “Generate a prompt to write pytest tests for selected project modules/functions, including relevant signatures and docstrings.”
- US2 (docs): “Generate a prompt to have an LLM write documentation (README/HowTo/API descriptions/docstrings) based on the specified code/files.”
- US3 (design): “Generate a prompt for an architecture/design discussion of the project: directory structure, key modules, dependencies, and potential extension points.”


## 4. Architecture (overview)

Layers:
- CLI layer (Typer): handle commands/flags, validate input paths, route to generators.
- Context layer: Scanner (file discovery), Parser (Python AST), Extractor (assemble context on demand).
- Templates (Jinja2): base templates for the three domains, language and style support.
- Output: stdout, pbcopy (macOS), save to file, formatted preview (optional, Rich).
- Limits/quotas: centralized limits for content size and trimming strategies.

Data flow:
CLI → Config → Scanner → Parser → Context Extractor → Template Renderer → Output (stdout/copy/file)


## 5. Components

1) CLI (Typer)
- Commands: tests, docs, design
- Common options: `--lang en` (default: en), `--style {concise|thorough|step-by-step}` (default: thorough), `--copy`, `--out PATH`, `--max-chars INT`, `--config PATH`, `--debug`.
- Arguments: list of `paths` (files/directories) to extract context from.

2) Config Manager
- Sources: `.ai-agent/config.yaml` at project root (if present), then environment variables, then defaults.
- Example keys: excludes, lang, style, max_chars, max_functions_per_module, include_private.

```yaml path=null start=null
# .ai-agent/config.yaml (example)
lang: ru
style: thorough
max_chars: 12000
include_private: false
max_functions_per_module: 8
excludes:
  - .git/**
  - .venv/**
  - __pycache__/**
  - node_modules/**
```

3) Scanner
- Based on pathspec patterns and explicit user paths.
- Looks for: for tests — .py files; for docs — .py, .md, .rst, .txt; for design — any, but summarizes the directory tree.
- Excludes by the `excludes` list from config plus sane defaults.

4) Parser (Python AST)
- Extracts: modules, classes, functions, signatures, docstrings, line/column (lineno, end_lineno), imports.
- Collects short code snippets per function (trimmed by limits) and metadata.
- Resilient to syntax errors (skip problematic files, warn in logs).

5) Context Extractor
- Combines scanning and parsing; applies prioritization heuristics (public functions above private, item count limits, sort by size/recency in future revisions).
- Produces structures for templates: project summary, list of modules with functions/classes, docstring excerpts.

6) Template Engine (Jinja2)
- Base layout: Role, Goal, Context, Constraints, Steps, Output format, DoD.
- Template variants: tests, docs, design (ru/en), styles: concise/thorough/step‑by‑step.
- Safe rendering with centralized size control (trim to max_chars).

7) Output Manager
- stdout: plain prompt text without formatting.
- pbcopy: via `subprocess` and the `pbcopy` command (macOS only; graceful fallback).
- file: save the result to `--out` or to `prompts/YYYY-MM-DD/HHMMSS-<cmd>.txt`.
- Rich (optional): colored preview that does not affect final text.

9) LLM Integration (LangChain)
- Provider: LM Studio (OpenAI‑compatible). Config via `llm_*` fields and `AI_AGENT_LLM_*` envs.
- Implementation: thin wrapper `LLMClient` using `langchain-openai.ChatOpenAI` with `base_url`.
- CLI flag `--run` on each command sends the rendered prompt and prints the model response.

8) Limits/Quotas
- Centralized module with limits on characters, item counts, and tree depth.
- Strategies: prioritization, context reduction, “summary instead of full code”.


## 6. CLI design and options

Examples (planned behavior):

```bash path=null start=null
# Generate a prompt for pytest based on specified files/directories
ai-agent tests src/ module_a.py --lang en --style thorough --copy --out prompts/

# Generate a prompt for documentation
ai-agent docs src/README.md src/ --lang en --style step-by-step

# Generate a prompt for architecture/design
ai-agent design . --lang en --style concise --max-chars 10000
```

Tests command extra flags:
- `--include-private/--no-include-private` (default false)
- `--pytest-scope {unit|integration}` (meta-hints for the template)

Docs command ideas:
- `--doc-type {readme|howto|api|docstrings}`

Design command ideas:
- `--include-deps` (future: attempt to infer import relationships)


## 7. Data structures (sketch)

- FunctionInfo: name, args, returns, decorators, is_public, docstring, snippet, lineno, end_lineno, module_path.
- ClassInfo: name, bases, methods[FunctionInfo], docstring.
- ModuleInfo: path, imports, functions[List[FunctionInfo]], classes[List[ClassInfo]], docstring.
- ProjectContext: modules[List[ModuleInfo]], tree_summary, stats.


## 8. Prompt templates (sketches)

Base layout:

```jinja path=null start=null
Role: You are an experienced {{ role }}.
Goal: {{ goal }}

Context:
{{ context }}

Constraints:
- Be precise; avoid speculation
- Ask clarifying questions when data is insufficient
- Response language: {{ lang }}

Steps:
{{ steps }}

Output format:
{{ output_format }}

Definition of Done:
{{ dod }}
```

Specialization for tests (pytest):

```jinja path=null start=null
{% set role = "Python developer experienced with pytest" %}
{% set goal = "Write high‑quality unit tests (pytest) for the specified modules/functions" %}

# Project context (snippets)
{{ project_summary }}

# Modules and functions
{{ modules_overview }}

# Test requirements
- Cover positive, negative, and edge‑case scenarios
- Use parametrization, fixtures, and marks when appropriate
- Minimize unnecessary mocking; isolate external IO
- Structure: arrange‑act‑assert

# Request to the model
- First propose a test plan (list of cases)
- Then generate test code (pytest) with brief comments on key decisions
```

Specialization for docs:

```jinja path=null start=null
{% set role = "Technical writer" %}
{% set goal = "Prepare the specified type of documentation based on the provided code/files" %}

Document type: {{ doc_type }}
Target audience: {{ audience }}
Tone: {{ tone }}

Materials:
{{ materials_summary }}

Requirements:
- Structure sections; add a table of contents if needed
- Include usage examples
- Keep terminology and names consistent
```

Specialization for design:

```jinja path=null start=null
{% set role = "System architect" %}
{% set goal = "Analyze the current architecture and propose improvements/design" %}

Project summary:
{{ tree_overview }}

Key components and responsibilities:
{{ components_summary }}

Problems and risks, optimization opportunities:
{{ risks_opportunities }}

Expected result:
- Brief architectural diagram (text)
- List of improvements with priorities
- Step‑by‑step implementation plan
```


## 9. Error handling and resilience

- Unreadable files: warn and skip.
- Size limits: safe trimming with a note that context was reduced.
- No pbcopy available: print a warning and continue without copying.
- Empty selection: clear message to the user (no matching files).


## 10. Performance

- Limit depth and context size by default.
- Scan only requested paths; apply excludes.
- AST parsing only for .py files; other files receive a textual summary/counts.


## 11. Security and privacy

- All operations are local; no network calls.
- Read only from specified paths; honor excludes.
- No metrics/telemetry collection.


## 12. Extensibility

- Add new templates (new domains, styles, languages) via the templates directory.
- Add additional analyzers (e.g., import graph) via separate modules.


## 13. Acceptance criteria (DoD)

- tests/docs/design commands work correctly on a demo project.
- Prompts contain structured sections and correct language/style.
- Context is extracted and limited per rules without errors or hangs.
- Clipboard copy (macOS) and file saving work.
- Configuration via file and environment variables affects behavior.


## 14. Risks and mitigations

- Very large projects → aggressive limiting and summaries.
- Inconsistent code styles → rely on AST and minimal heuristics.
- Diverse documentation formats → rely on general structure and user parameters.


## 15. Future

- Optional LM Studio integration for preview/iterations.
- Support for other languages/frameworks for tests (JS, Go, Java).
- Rich dependency analyzers and coverage‑aware prompts.

