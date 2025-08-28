from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Literal, Sequence

import os

from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

Domain = Literal["tests", "docs", "design"]


@dataclass(frozen=True)
class ScanResult:
    files: List[Path]


_DEFAULT_EXTENSIONS = {
    "tests": {".py"},
    "docs": {".py", ".md", ".rst", ".txt"},
    "design": None,  # all files, but we will summarize tree rather than content
}


def _build_spec(excludes: Sequence[str]) -> PathSpec:
    return PathSpec.from_lines(GitWildMatchPattern, excludes)


def _iter_files(paths: Sequence[Path]) -> Iterable[Path]:
    for p in paths:
        if p.is_file():
            yield p
        elif p.is_dir():
            for root, _dirs, files in os.walk(p, topdown=True):
                root_path = Path(root)
                for name in files:
                    yield root_path / name


def scan_paths(paths: Sequence[Path], excludes: Sequence[str], domain: Domain) -> ScanResult:
    if not paths:
        return ScanResult(files=[])

    norm_paths = [p.resolve() for p in paths]
    spec = _build_spec(excludes)
    exts = _DEFAULT_EXTENSIONS[domain]

    selected: List[Path] = []
    for file_path in _iter_files(norm_paths):
        try:
            rel = file_path.relative_to(Path.cwd())
        except Exception:
            # If outside cwd, use absolute path for matching
            rel = file_path
        rel_str = str(rel)
        if spec.match_file(rel_str):
            continue
        if exts is not None and file_path.suffix not in exts:
            continue
        selected.append(file_path)

    return ScanResult(files=selected)


def summarize_tree(paths: Sequence[Path], excludes: Sequence[str], max_depth: int = 4, max_entries: int = 500) -> str:
    """Produce a simple textual tree summary for design prompts.
    Limits depth and number of entries for safety.
    """
    spec = _build_spec(excludes)
    lines: List[str] = []

    def _walk(base: Path, prefix: str, depth: int, entries_count: int) -> int:
        if depth > max_depth or entries_count >= max_entries:
            return entries_count
        try:
            entries = sorted(list(base.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
        except Exception:
            return entries_count
        for i, entry in enumerate(entries):
            rel = entry.relative_to(Path.cwd()) if entry.is_absolute() else entry
            rel_str = str(rel)
            if spec.match_file(rel_str):
                continue
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(prefix + connector + entry.name)
            entries_count += 1
            if entries_count >= max_entries:
                break
            if entry.is_dir():
                next_prefix = prefix + ("    " if i == len(entries) - 1 else "│   ")
                entries_count = _walk(entry, next_prefix, depth + 1, entries_count)
                if entries_count >= max_entries:
                    break
        return entries_count

    for p in paths:
        base = p.resolve()
        if not base.exists():
            continue
        lines.append(str(base.name))
        _walk(base, "", 1, 0)

    if len(lines) >= max_entries:
        lines.append("… (truncated)")

    return "\n".join(lines)

