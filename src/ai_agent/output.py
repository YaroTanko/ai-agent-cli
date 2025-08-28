from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import subprocess


@dataclass
class OutputOptions:
    copy_to_clipboard: bool = False
    out_path: Optional[Path] = None
    base_dir: Path = Path.cwd()
    command_name: str = "prompt"


def _ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def save_prompt(text: str, options: OutputOptions) -> Optional[Path]:
    if options.out_path:
        path = options.out_path
    else:
        now = datetime.now()
        path = options.base_dir / "prompts" / now.strftime("%Y-%m-%d") / f"{now.strftime('%H%M%S')}-{options.command_name}.txt"
    _ensure_dir(path)
    path.write_text(text, encoding="utf-8")
    return path


def copy_to_clipboard(text: str) -> bool:
    try:
        proc = subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        return proc.returncode == 0
    except Exception:
        return False


def emit(text: str, options: OutputOptions) -> Optional[Path]:
    # Always print to stdout (plain text)
    print(text)

    # Optionally copy
    if options.copy_to_clipboard:
        ok = copy_to_clipboard(text)
        if not ok:
            print("[warn] pbcopy is unavailable — skipping clipboard copy", flush=True)

    # Save only if explicit out_path provided
    if options.out_path is not None:
        return save_prompt(text, options)
    return None

