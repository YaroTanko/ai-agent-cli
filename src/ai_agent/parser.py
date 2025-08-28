from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import ast

from .limits import Limits


@dataclass
class FunctionInfo:
    name: str
    args: List[str]
    returns: Optional[str]
    decorators: List[str]
    is_public: bool
    docstring: Optional[str]
    snippet: Optional[str]
    lineno: int
    end_lineno: int


@dataclass
class ClassInfo:
    name: str
    bases: List[str]
    methods: List[FunctionInfo] = field(default_factory=list)
    docstring: Optional[str] = None
    lineno: int = 0
    end_lineno: int = 0


@dataclass
class ModuleInfo:
    path: Path
    imports: List[str]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    docstring: Optional[str]


def _get_source_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []


def _extract_snippet(lines: List[str], start: int, end: int, limits: Limits) -> str:
    # ast lineno are 1-based inclusive
    start_idx = max(0, start - 1)
    end_idx = min(len(lines), end)
    snippet_lines = lines[start_idx:end_idx]
    if len(snippet_lines) > limits.snippet_max_lines:
        snippet_lines = snippet_lines[: limits.snippet_max_lines]
        snippet_lines.append("# ... (truncated)")
    return "\n".join(snippet_lines)


def _ann_to_str(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)  # Python 3.9+: returns a string representation
    except Exception:
        return None


def _args_from_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> List[str]:
    params: List[str] = []
    args = node.args
    for a in args.posonlyargs:
        params.append(a.arg)
    for a in args.args:
        params.append(a.arg)
    if args.vararg:
        params.append("*" + args.vararg.arg)
    for a in args.kwonlyargs:
        params.append(a.arg)
    if args.kwarg:
        params.append("**" + args.kwarg.arg)
    return params


def _decorators(node: ast.AST) -> List[str]:
    decs: List[str] = []
    for d in getattr(node, "decorator_list", []) or []:
        try:
            decs.append(ast.unparse(d))
        except Exception:
            pass
    return decs


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def parse_module(path: Path, limits: Optional[Limits] = None) -> Optional[ModuleInfo]:
    limits = limits or Limits()
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return None

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    lines = source.splitlines()

    module_doc = ast.get_docstring(tree)

    imports: List[str] = []
    functions: List[FunctionInfo] = []
    classes: List[ClassInfo] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            try:
                imports.append(ast.unparse(node))
            except Exception:
                pass
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            doc = ast.get_docstring(node)
            args = _args_from_function(node)
            returns = _ann_to_str(node.returns)
            decs = _decorators(node)
            lineno = getattr(node, "lineno", 1)
            end_lineno = getattr(node, "end_lineno", lineno)
            snippet = _extract_snippet(lines, lineno, end_lineno, limits)
            functions.append(
                FunctionInfo(
                    name=name,
                    args=args,
                    returns=returns,
                    decorators=decs,
                    is_public=_is_public(name),
                    docstring=(doc[: limits.docstring_max_chars] if doc else None),
                    snippet=snippet,
                    lineno=lineno,
                    end_lineno=end_lineno,
                )
            )
        elif isinstance(node, ast.ClassDef):
            name = node.name
            doc = ast.get_docstring(node)
            bases: List[str] = []
            for b in node.bases:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    pass
            lineno = getattr(node, "lineno", 1)
            end_lineno = getattr(node, "end_lineno", lineno)
            ci = ClassInfo(
                name=name,
                bases=bases,
                methods=[],
                docstring=(doc[: limits.docstring_max_chars] if doc else None),
                lineno=lineno,
                end_lineno=end_lineno,
            )
            # methods
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_doc = ast.get_docstring(m)
                    m_args = _args_from_function(m)
                    m_returns = _ann_to_str(m.returns)
                    m_decs = _decorators(m)
                    m_lineno = getattr(m, "lineno", 1)
                    m_end = getattr(m, "end_lineno", m_lineno)
                    m_snippet = _extract_snippet(lines, m_lineno, m_end, limits)
                    ci.methods.append(
                        FunctionInfo(
                            name=m.name,
                            args=m_args,
                            returns=m_returns,
                            decorators=m_decs,
                            is_public=_is_public(m.name),
                            docstring=(m_doc[: limits.docstring_max_chars] if m_doc else None),
                            snippet=m_snippet,
                            lineno=m_lineno,
                            end_lineno=m_end,
                        )
                    )
            classes.append(ci)

    return ModuleInfo(
        path=path,
        imports=imports,
        functions=functions,
        classes=classes,
        docstring=(module_doc[: limits.docstring_max_chars] if module_doc else None),
    )


__all__ = [
    "FunctionInfo",
    "ClassInfo",
    "ModuleInfo",
    "parse_module",
]

