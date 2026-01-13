from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List

RESULTS_DIR = Path("storage") / "results"

def _path(deal_id: str) -> Path:
    d = RESULTS_DIR / deal_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "doc_index.json"

def load_doc_index(deal_id: str) -> List[Dict[str, Any]]:
    p = _path(deal_id)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []

def upsert_doc(deal_id: str, doc: Dict[str, Any]) -> None:
    arr = load_doc_index(deal_id)
    key = (doc.get("doc_id"), doc.get("filename"))
    updated = False
    for i, d in enumerate(arr):
        if (d.get("doc_id"), d.get("filename")) == key:
            arr[i] = {**d, **doc}
            updated = True
            break
    if not updated:
        arr.append(doc)
    _path(deal_id).write_text(json.dumps(arr, indent=2), encoding="utf-8")
