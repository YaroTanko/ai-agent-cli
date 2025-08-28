from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from .parser import ModuleInfo, parse_module
from .limits import Limits


@dataclass
class ProjectContext:
    modules: List[ModuleInfo]
    tree_summary: Optional[str] = None
    stats: Optional[str] = None


def build_python_context(paths: Sequence[Path], limits: Optional[Limits] = None) -> ProjectContext:
    """Parse Python files into ModuleInfo items.
    This function expects `paths` to already be filtered to Python files.
    """
    limits = limits or Limits()
    modules: List[ModuleInfo] = []
    for p in paths:
        mi = parse_module(p, limits=limits)
        if mi is not None:
            modules.append(mi)
        if len(modules) >= limits.max_modules:
            break

    # Simple stats
    total_funcs = sum(len(m.functions) for m in modules)
    total_classes = sum(len(m.classes) for m in modules)
    stats = f"modules={len(modules)}, functions={total_funcs}, classes={total_classes}"

    return ProjectContext(modules=modules, stats=stats)


def summarize_modules(modules: Sequence[ModuleInfo], limits: Optional[Limits] = None) -> str:
    """Produce a textual overview of modules and top functions/classes.
    Applies simple prioritization: public first, then private, up to per-module limits.
    """
    limits = limits or Limits()
    lines: List[str] = []
    for m in modules:
        lines.append(f"- Module: {m.path}")
        # module docstring (trimmed)
        if m.docstring:
            lines.append(f"  Doc: {m.docstring[:200].strip()}...")
        # functions
        pub_funcs = [f for f in m.functions if f.is_public]
        priv_funcs = [f for f in m.functions if not f.is_public]
        chosen_funcs = (pub_funcs + priv_funcs)[: limits.max_funcs_per_module]
        for fn in chosen_funcs:
            sig = f"({', '.join(fn.args)})"
            ret = f" -> {fn.returns}" if fn.returns else ""
            lines.append(f"  * def {fn.name}{sig}{ret}")
            if fn.docstring:
                lines.append(f"    Doc: {fn.docstring[:160].strip()}...")
        # classes
        chosen_classes = m.classes[: limits.max_classes_per_module]
        for cl in chosen_classes:
            base_str = f"({', '.join(cl.bases)})" if cl.bases else ""
            lines.append(f"  * class {cl.name}{base_str}")
            if cl.docstring:
                lines.append(f"    Doc: {cl.docstring[:160].strip()}...")
            # methods (public first)
            pub_methods = [mm for mm in cl.methods if mm.is_public]
            priv_methods = [mm for mm in cl.methods if not mm.is_public]
            chosen_methods = (pub_methods + priv_methods)[: limits.max_funcs_per_module]
            for mn in chosen_methods:
                msig = f"({', '.join(mn.args)})"
                mret = f" -> {mn.returns}" if mn.returns else ""
                lines.append(f"    - def {mn.name}{msig}{mret}")
    return "\n".join(lines)

