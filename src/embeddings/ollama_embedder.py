from __future__ import annotations
import requests

def embed_text_ollama(base_url: str, model: str, text: str, timeout_s: float = 60.0) -> list[float]:
    """
    Tries Ollama embed endpoints:
    - /api/embed (newer)
    - /api/embeddings (older)
    Returns a single embedding vector for `text`.
    """
    payload_embed = {"model": model, "input": text}
    r = requests.post(f"{base_url}/api/embed", json=payload_embed, timeout=timeout_s)
    if r.status_code == 200:
        data = r.json()
        # /api/embed returns: {"embeddings":[[...]]} for single input or list
        embs = data.get("embeddings", [])
        if not embs:
            raise RuntimeError("Ollama /api/embed returned no embeddings")
        return embs[0]

    # fallback older endpoint
    payload_old = {"model": model, "prompt": text}
    r2 = requests.post(f"{base_url}/api/embeddings", json=payload_old, timeout=timeout_s)
    if r2.status_code != 200:
        raise RuntimeError(f"Ollama embedding failed: /api/embed HTTP {r.status_code} and /api/embeddings HTTP {r2.status_code}: {r2.text[:200]}")
    data2 = r2.json()
    emb = data2.get("embedding", None)
    if emb is None:
        raise RuntimeError("Ollama /api/embeddings returned no 'embedding'")
    return emb