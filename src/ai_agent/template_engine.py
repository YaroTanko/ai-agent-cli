from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, StrictUndefined


_STYLE_TEXT_EN = {
    "concise": "Be concise (3–7 bullets), avoid fluff.",
    "thorough": "Provide a detailed, structured answer with examples if needed.",
    "step-by-step": "Explain step-by-step, then present the final result.",
}


def _style_text(lang: str, style: str) -> str:
    return _STYLE_TEXT_EN.get(style, _STYLE_TEXT_EN["thorough"])  # English only


def _truncate(text: str, max_chars: Optional[int]) -> str:
    if not max_chars or max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 12].rstrip() + "\n... (truncated)"


@dataclass
class TemplateEngine:
    templates_dir: Path

    def __post_init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
            undefined=StrictUndefined,
            trim_blocks=False,
            lstrip_blocks=False,
        )

    def _template_path(self, domain: str, lang: str) -> str:
        if domain == "tests":
            return "tests/pytest_en.j2"
        elif domain == "docs":
            return "docs/docs_en.j2"
        elif domain == "design":
            return "design/design_en.j2"
        raise ValueError(f"Unknown domain: {domain}")

    def render(self, domain: str, lang: str, style: str, context: Dict[str, Any], max_chars: Optional[int] = None) -> str:
        # enrich context with style text
        context = dict(context)
        context.setdefault("lang", lang)
        context["style_text"] = _style_text(lang, style)

        tpl_name = self._template_path(domain, lang)
        tpl = self.env.get_template(tpl_name)
        text = tpl.render(**context)
        return _truncate(text, max_chars)

