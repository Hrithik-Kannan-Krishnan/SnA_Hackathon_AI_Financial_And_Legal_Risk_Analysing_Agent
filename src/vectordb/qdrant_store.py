from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from qdrant_client import QdrantClient

@lru_cache(maxsize=4)
def get_qdrant_local_client_cached(path_str: str) -> QdrantClient:
    # One client per path per process
    return QdrantClient(path=path_str)

def get_qdrant_local_client(path: Path) -> QdrantClient:
    return get_qdrant_local_client_cached(str(path.resolve()))

def qdrant_healthcheck(path: Path) -> tuple[bool, str]:
    try:
        client = get_qdrant_local_client(path)
        cols = client.get_collections().collections
        names = [c.name for c in cols]
        if names:
            return True, f"OK (collections: {', '.join(names[:5])}{'...' if len(names) > 5 else ''})"
        return True, "OK (no collections yet)"
    except Exception as e:
        return False, f"Failed: {e}"