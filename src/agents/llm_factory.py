from __future__ import annotations

from src.core.settings import get_settings

def get_llm_id() -> str:
    """
    CrewAI supports setting llm as a STRING identifier (recommended when LLM class isn't available).
    Example: "ollama/qwen2.5:7b"
    """
    s = get_settings()
    return f"ollama/{s.chat_model}"
