from __future__ import annotations
import requests

def ollama_healthcheck(base_url: str, timeout_s: float = 2.5) -> tuple[bool, str]:
    """Returns (ok, message). Uses /api/tags to verify Ollama is reachable."""
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=timeout_s)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
        data = r.json()
        models = data.get("models", [])
        names = [m.get("name") for m in models if m.get("name")]
        if names:
            return True, f"OK (models: {', '.join(names[:5])}{'...' if len(names) > 5 else ''})"
        return True, "OK (no models pulled yet)"
    except Exception as e:
        return False, f"Not reachable: {e}"