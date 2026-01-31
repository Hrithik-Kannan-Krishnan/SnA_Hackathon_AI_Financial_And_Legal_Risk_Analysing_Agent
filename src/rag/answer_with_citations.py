from __future__ import annotations
from typing import List, Dict, Any

def build_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Creates a compact context block the model can cite.
    """
    parts = []
    for i, c in enumerate(chunks, start=1):
        fn = c.get("filename", "unknown")
        cid = c.get("chunk_id", "na")
        text = (c.get("text") or "").strip().replace("\n", " ")
        parts.append(f"[S{i}] {fn} (chunk {cid}): {text[:900]}")
    return "\n\n".join(parts)

SYSTEM_CITED = """You are a due diligence copilot.
Answer ONLY using the provided SOURCES.
If the sources are insufficient, say you couldn't find enough in the indexed docs.
When you make a claim, cite it like [S1], [S2] etc.
Keep it concise and factual.
"""

def format_sources(chunks: List[Dict[str, Any]]) -> str:
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(f"[S{i}] {c.get('filename')} (chunk {c.get('chunk_id')})")
    return "\n".join(lines)
