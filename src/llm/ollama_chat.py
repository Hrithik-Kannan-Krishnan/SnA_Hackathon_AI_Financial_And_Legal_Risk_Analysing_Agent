from __future__ import annotations
import requests

def ollama_chat(base_url: str, model: str, messages: list[dict], timeout_s: float = 120.0) -> str:
    """
    Uses Ollama /api/chat.
    messages = [{"role":"system|user|assistant", "content":"..."}]
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    r = requests.post(f"{base_url}/api/chat", json=payload, timeout=timeout_s)
    if r.status_code != 200:
        raise RuntimeError(f"Ollama chat failed HTTP {r.status_code}: {r.text[:200]}")
    data = r.json()
    msg = data.get("message", {})
    return msg.get("content", "").strip()