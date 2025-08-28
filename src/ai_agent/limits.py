from __future__ import annotations

from dataclasses import dataclass

# Centralized limits and strategies for truncation and selection

DEFAULT_MAX_CHARS = 12000
DEFAULT_MAX_FUNCS_PER_MODULE = 8
DEFAULT_MAX_CLASSES_PER_MODULE = 8
DEFAULT_MAX_MODULES = 50
DEFAULT_SNIPPET_MAX_LINES = 120
DEFAULT_DOCSTRING_MAX_CHARS = 1200


@dataclass(frozen=True)
class Limits:
    max_chars: int = DEFAULT_MAX_CHARS
    max_funcs_per_module: int = DEFAULT_MAX_FUNCS_PER_MODULE
    max_classes_per_module: int = DEFAULT_MAX_CLASSES_PER_MODULE
    max_modules: int = DEFAULT_MAX_MODULES
    snippet_max_lines: int = DEFAULT_SNIPPET_MAX_LINES
    docstring_max_chars: int = DEFAULT_DOCSTRING_MAX_CHARS

