from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import yaml


# Supported options and defaults
_DEFAULTS: Dict[str, Any] = {
    "lang": "en",  # en only
    "style": "thorough",  # concise | thorough | step-by-step
    "max_chars": 12000,
    "include_private": False,
    "max_functions_per_module": 8,
    "excludes": [
        ".git/**",
        ".venv/**",
        "__pycache__/**",
        "node_modules/**",
        "dist/**",
        "build/**",
    ],
    # LLM/LangChain defaults (LM Studio OpenAI-compatible)
    "llm_provider": "lm-studio",  # lm-studio | openai | ollama
    "llm_model": "gpt-4o-mini",   # LM Studio served model name
    "llm_base_url": "http://localhost:1234/v1",  # LM Studio OpenAI-compatible endpoint
    "llm_api_key": "lm-studio",   # LM Studio often ignores but required by some clients
    "llm_temperature": 0.2,
    "llm_max_tokens": 2048,
}

# Environment variables mapping
_ENV_MAP = {
    "lang": "AI_AGENT_LANG",
    "style": "AI_AGENT_STYLE",
    "max_chars": "AI_AGENT_MAX_CHARS",
    "include_private": "AI_AGENT_INCLUDE_PRIVATE",
    "max_functions_per_module": "AI_AGENT_MAX_FUNCS_PER_MODULE",
    # LLM envs
    "llm_provider": "AI_AGENT_LLM_PROVIDER",
    "llm_model": "AI_AGENT_LLM_MODEL",
    "llm_base_url": "AI_AGENT_LLM_BASE_URL",
    "llm_api_key": "AI_AGENT_LLM_API_KEY",
    "llm_temperature": "AI_AGENT_LLM_TEMPERATURE",
    "llm_max_tokens": "AI_AGENT_LLM_MAX_TOKENS",
}

_VALID_LANGS = {"en"}
_VALID_STYLES = {"concise", "thorough", "step-by-step"}


@dataclass
class Config:
    lang: str = _DEFAULTS["lang"]
    style: str = _DEFAULTS["style"]
    max_chars: int = _DEFAULTS["max_chars"]
    include_private: bool = _DEFAULTS["include_private"]
    max_functions_per_module: int = _DEFAULTS["max_functions_per_module"]
    excludes: List[str] = field(default_factory=lambda: list(_DEFAULTS["excludes"]))

    # LLM settings
    llm_provider: str = _DEFAULTS["llm_provider"]
    llm_model: str = _DEFAULTS["llm_model"]
    llm_base_url: str = _DEFAULTS["llm_base_url"]
    llm_api_key: str = _DEFAULTS["llm_api_key"]
    llm_temperature: float = _DEFAULTS["llm_temperature"]
    llm_max_tokens: int = _DEFAULTS["llm_max_tokens"]

    # Optional: path to explicit config file that was used
    source_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.source_path is not None:
            d["source_path"] = str(self.source_path)
        return d


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                return {}
            return data
    except FileNotFoundError:
        return {}
    except Exception:
        # Be resilient: ignore malformed YAML for MVP
        return {}


def _apply_env(overrides: Dict[str, Any]) -> Dict[str, Any]:
    env_overrides: Dict[str, Any] = {}
    for key, env_key in _ENV_MAP.items():
        raw = os.environ.get(env_key)
        if raw is None:
            continue
        if key in {"max_chars", "max_functions_per_module", "llm_max_tokens"}:
            try:
                env_overrides[key] = int(raw)
            except ValueError:
                continue
        elif key == "include_private":
            env_overrides[key] = raw.lower() in {"1", "true", "yes", "on"}
        elif key == "llm_temperature":
            try:
                env_overrides[key] = float(raw)
            except ValueError:
                continue
        else:
            env_overrides[key] = raw
    return _deep_merge(overrides, env_overrides)


def _validate(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize/validate lang
    lang = str(cfg.get("lang", _DEFAULTS["lang"]))
    if lang not in _VALID_LANGS:
        lang = _DEFAULTS["lang"]

    # Normalize/validate style
    style = str(cfg.get("style", _DEFAULTS["style"]))
    if style not in _VALID_STYLES:
        style = _DEFAULTS["style"]

    # Numeric fields
    try:
        max_chars = int(cfg.get("max_chars", _DEFAULTS["max_chars"]))
    except Exception:
        max_chars = _DEFAULTS["max_chars"]
    try:
        max_fpm = int(cfg.get("max_functions_per_module", _DEFAULTS["max_functions_per_module"]))
    except Exception:
        max_fpm = _DEFAULTS["max_functions_per_module"]

    include_private = bool(cfg.get("include_private", _DEFAULTS["include_private"]))

    # Excludes list
    excludes = cfg.get("excludes", _DEFAULTS["excludes"])
    if not isinstance(excludes, list):
        excludes = list(_DEFAULTS["excludes"])  # copy

    # LLM settings
    llm_provider = str(cfg.get("llm_provider", _DEFAULTS["llm_provider"]))
    if llm_provider not in {"lm-studio", "openai", "ollama"}:
        llm_provider = _DEFAULTS["llm_provider"]
    llm_model = str(cfg.get("llm_model", _DEFAULTS["llm_model"]))
    llm_base_url = str(cfg.get("llm_base_url", _DEFAULTS["llm_base_url"]))
    llm_api_key = str(cfg.get("llm_api_key", _DEFAULTS["llm_api_key"]))
    try:
        llm_temperature = float(cfg.get("llm_temperature", _DEFAULTS["llm_temperature"]))
    except Exception:
        llm_temperature = _DEFAULTS["llm_temperature"]
    try:
        llm_max_tokens = int(cfg.get("llm_max_tokens", _DEFAULTS["llm_max_tokens"]))
    except Exception:
        llm_max_tokens = _DEFAULTS["llm_max_tokens"]

    return {
        "lang": lang,
        "style": style,
        "max_chars": max_chars,
        "include_private": include_private,
        "max_functions_per_module": max_fpm,
        "excludes": excludes,
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "llm_base_url": llm_base_url,
        "llm_api_key": llm_api_key,
        "llm_temperature": llm_temperature,
        "llm_max_tokens": llm_max_tokens,
    }


def load_config(cwd: Optional[Path] = None, explicit_config_path: Optional[Path] = None) -> Config:
    """Load configuration with the following precedence:
    - Defaults (built-in)
    - File at explicit_config_path if provided
    - File at <cwd>/.ai-agent/config.yaml if present
    - Environment variables (AI_AGENT_*)
    """
    cwd = cwd or Path.cwd()
    data: Dict[str, Any] = dict(_DEFAULTS)
    source_path: Optional[Path] = None

    # explicit file
    if explicit_config_path:
        file_data = _load_yaml(explicit_config_path)
        data = _deep_merge(data, file_data)
        source_path = explicit_config_path

    # project file
    else:
        candidate = cwd / ".ai-agent" / "config.yaml"
        if candidate.exists():
            file_data = _load_yaml(candidate)
            data = _deep_merge(data, file_data)
            source_path = candidate

    # environment overrides
    data = _apply_env(data)

    # validate
    v = _validate(data)

    return Config(
        lang=v["lang"],
        style=v["style"],
        max_chars=v["max_chars"],
        include_private=v["include_private"],
        max_functions_per_module=v["max_functions_per_module"],
        excludes=v["excludes"],
        llm_provider=v["llm_provider"],
        llm_model=v["llm_model"],
        llm_base_url=v["llm_base_url"],
        llm_api_key=v["llm_api_key"],
        llm_temperature=v["llm_temperature"],
        llm_max_tokens=v["llm_max_tokens"],
        source_path=source_path,
    )

