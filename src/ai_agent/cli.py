from __future__ import annotations

import sys
from pathlib import Path
import typer

from .config import load_config
from .limits import Limits
from .scanner import scan_paths, summarize_tree
from .extractor import build_python_context, summarize_modules
from .template_engine import TemplateEngine
from .output import OutputOptions, emit
from .llm import LLMClient


app = typer.Typer(add_completion=False, help="AI-Agent CLI: generate prompts for tests, docs, and design")


def _engine() -> TemplateEngine:
    # Try CWD/templates first (developer-friendly), then project root relative to package
    candidates = [
        Path.cwd() / "templates",
        Path(__file__).resolve().parents[2] / "templates",
    ]
    for c in candidates:
        if c.exists():
            return TemplateEngine(templates_dir=c)
    # Fallback: package-internal templates path (if later moved into package)
    fallback = Path(__file__).resolve().parent / "templates"
    return TemplateEngine(templates_dir=fallback)


def _limits_from_config(cfg) -> Limits:
    return Limits(
        max_chars=cfg.max_chars,
        max_funcs_per_module=cfg.max_functions_per_module,
        # keep defaults for other fields for now
    )


@app.callback()
def main_callback(
    ctx: typer.Context,
    config: Path = typer.Option(None, "--config", help="Path to config YAML"),
    lang: str = typer.Option(None, "--lang", help="en"),
    style: str = typer.Option(None, "--style", help="concise|thorough|step-by-step"),
    max_chars: int = typer.Option(None, "--max-chars", help="Max characters in prompt"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug prints"),
):
    """Load configuration and store in context."""
    cwd = Path.cwd()
    cfg = load_config(cwd=cwd, explicit_config_path=config)

    # runtime overrides
    if lang:
        cfg.lang = lang
    if style:
        cfg.style = style
    if max_chars is not None:
        cfg.max_chars = int(max_chars)

    ctx.ensure_object(dict)
    ctx.obj["cfg"] = cfg
    ctx.obj["limits"] = _limits_from_config(cfg)
    ctx.obj["engine"] = _engine()
    ctx.obj["debug"] = debug


@app.command()
def tests(
    ctx: typer.Context,
    paths: list[Path] = typer.Argument(..., help="Files or directories to include"),
    include_private: bool = typer.Option(None, "--include-private/--no-include-private", help="Include private members"),
    pytest_scope: str = typer.Option("unit", "--pytest-scope", help="Meta: unit|integration"),
    copy: bool = typer.Option(False, "--copy", help="Copy to clipboard"),
    run: bool = typer.Option(False, "--run", help="Send prompt to LLM and print the answer"),
    out: Path = typer.Option(None, "--out", help="Save prompt to a file or directory"),
):
    cfg = ctx.obj["cfg"]
    limits: Limits = ctx.obj["limits"]
    engine: TemplateEngine = ctx.obj["engine"]

    if include_private is not None:
        cfg.include_private = include_private

    scan = scan_paths(paths, cfg.excludes, domain="tests")
    if not scan.files:
        typer.echo("[error] No suitable files found for analysis", err=True)
        raise typer.Exit(code=2)

    project_ctx = build_python_context(scan.files, limits=limits)
    modules_overview = summarize_modules(project_ctx.modules, limits=limits)

    context = {
        "project_summary": project_ctx.stats,
        "modules_overview": modules_overview,
        "pytest_scope": pytest_scope,
        "lang": cfg.lang,
    }
    prompt = engine.render(domain="tests", lang=cfg.lang, style=cfg.style, context=context, max_chars=cfg.max_chars)

    out_path = out
    if out_path and out_path.is_dir():
        out_path = out_path / "prompt-tests.txt"

    if run:
        llm = LLMClient(cfg)
        result = llm.complete(prompt)
        typer.echo("\n=== LLM Response ===\n" + result.text)

    emit(prompt, OutputOptions(copy_to_clipboard=copy, out_path=out_path, base_dir=Path.cwd(), command_name="tests"))


@app.command()
def docs(
    ctx: typer.Context,
    paths: list[Path] = typer.Argument(..., help="Files or directories to include"),
    doc_type: str = typer.Option("readme", "--doc-type", help="readme|howto|api|docstrings"),
    audience: str = typer.Option("developers", "--audience", help="target audience"),
    tone: str = typer.Option("neutral", "--tone", help="tone of voice"),
    copy: bool = typer.Option(False, "--copy", help="Copy to clipboard"),
    run: bool = typer.Option(False, "--run", help="Send prompt to LLM and print the answer"),
    out: Path = typer.Option(None, "--out", help="Save prompt to a file or directory"),
):
    cfg = ctx.obj["cfg"]
    limits: Limits = ctx.obj["limits"]
    engine: TemplateEngine = ctx.obj["engine"]

    scan = scan_paths(paths, cfg.excludes, domain="docs")
    if not scan.files:
        typer.echo("[error] No suitable files found for analysis", err=True)
        raise typer.Exit(code=2)

    # For docs, parse .py files and list non-py textual files
    py_files = [p for p in scan.files if p.suffix == ".py"]
    other_files = [p for p in scan.files if p.suffix != ".py"]

    project_ctx = build_python_context(py_files, limits=limits)
    modules_overview = summarize_modules(project_ctx.modules, limits=limits)

    # summarize other files names
    other_summary = "\n".join(f"- {p}" for p in other_files[:100])

    context = {
        "materials_summary": modules_overview + ("\n\nOther materials:\n" + other_summary if other_summary else ""),
        "doc_type": doc_type,
        "audience": audience,
        "tone": tone,
        "lang": cfg.lang,
    }

    prompt = engine.render(domain="docs", lang=cfg.lang, style=cfg.style, context=context, max_chars=cfg.max_chars)

    out_path = out
    if out_path and out_path.is_dir():
        out_path = out_path / "prompt-docs.txt"

    if run:
        llm = LLMClient(cfg)
        result = llm.complete(prompt)
        typer.echo("\n=== LLM Response ===\n" + result.text)

    emit(prompt, OutputOptions(copy_to_clipboard=copy, out_path=out_path, base_dir=Path.cwd(), command_name="docs"))


@app.command()
def design(
    ctx: typer.Context,
    paths: list[Path] = typer.Argument(..., help="Files or directories to include"),
    copy: bool = typer.Option(False, "--copy", help="Copy to clipboard"),
    run: bool = typer.Option(False, "--run", help="Send prompt to LLM and print the answer"),
    out: Path = typer.Option(None, "--out", help="Save prompt to a file or directory"),
):
    cfg = ctx.obj["cfg"]
    limits: Limits = ctx.obj["limits"]
    engine: TemplateEngine = ctx.obj["engine"]

    # For design, we focus on directory structure and high-level overview
    tree = summarize_tree(paths, cfg.excludes)

    # Also include python modules overview if present
    scan = scan_paths(paths, cfg.excludes, domain="tests")
    project_ctx = build_python_context(scan.files, limits=limits) if scan.files else None
    modules_overview = summarize_modules(project_ctx.modules, limits=limits) if project_ctx else ""

    context = {
        "tree_overview": tree,
        "components_summary": modules_overview,
        "risks_opportunities": "",
        "lang": cfg.lang,
    }

    prompt = engine.render(domain="design", lang=cfg.lang, style=cfg.style, context=context, max_chars=cfg.max_chars)

    out_path = out
    if out_path and out_path.is_dir():
        out_path = out_path / "prompt-design.txt"

    if run:
        llm = LLMClient(cfg)
        result = llm.complete(prompt)
        typer.echo("\n=== LLM Response ===\n" + result.text)

    emit(prompt, OutputOptions(copy_to_clipboard=copy, out_path=out_path, base_dir=Path.cwd(), command_name="design"))


if __name__ == "__main__":
    app()

