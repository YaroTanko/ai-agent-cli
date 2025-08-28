from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import Config


@dataclass
class LLMResult:
    text: str


class LLMClient:
    """Thin wrapper over LangChain to call an LLM.

    For LM Studio, we assume an OpenAI-compatible endpoint at cfg.llm_base_url.
    """

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._ensure_langchain()
        self._llm = self._build_llm()

    def _ensure_langchain(self) -> None:
        try:
            import langchain  # noqa: F401
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "LangChain is not installed. Please install dependencies (see pyproject)."
            ) from e

    def _build_llm(self):
        # Lazy import to avoid hard dependency during CLI-only prompt generation
        from langchain_openai import ChatOpenAI

        if self.cfg.llm_provider == "lm-studio":
            # LM Studio exposes OpenAI-compatible API
            return ChatOpenAI(
                model=self.cfg.llm_model,
                base_url=self.cfg.llm_base_url,
                api_key=self.cfg.llm_api_key,
                temperature=self.cfg.llm_temperature,
                max_tokens=self.cfg.llm_max_tokens,
            )
        elif self.cfg.llm_provider == "openai":
            return ChatOpenAI(
                model=self.cfg.llm_model,
                api_key=self.cfg.llm_api_key,
                temperature=self.cfg.llm_temperature,
                max_tokens=self.cfg.llm_max_tokens,
            )
        else:
            # Future: add Ollama via langchain_community.chat_models.ChatOllama
            raise ValueError(f"Unsupported llm_provider: {self.cfg.llm_provider}")

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResult:
        from langchain_core.messages import SystemMessage, HumanMessage

        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        response = self._llm.invoke(messages)
        # ChatOpenAI returns BaseMessage; get content
        text = getattr(response, "content", str(response))
        return LLMResult(text=text)


