from __future__ import annotations

import requests
from typing import List

def embed_text(base_url: str, model: str, text: str, timeout_s: float = 60.0) -> List[float]:
    """
    Calls Ollama embeddings API:
      POST /api/embeddings  { "model": "...", "prompt": "..." }
    Returns a vector list[float].
    """
    payload = {"model": model, "prompt": text}
    r = requests.post(f"{base_url}/api/embeddings", json=payload, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    vec = data.get("embedding")
    if not isinstance(vec, list) or not vec:
        raise RuntimeError(f"No embedding returned from Ollama. Response: {str(data)[:200]}")
    return vec
