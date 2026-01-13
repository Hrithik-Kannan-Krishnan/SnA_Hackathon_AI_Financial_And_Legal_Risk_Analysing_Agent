from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List

RESULTS_DIR = Path("storage") / "results"

def _deal_dir(deal_id: str) -> Path:
    d = RESULTS_DIR / deal_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def load_legal_results(deal_id: str) -> List[Dict[str, Any]]:
    return _read_json(_deal_dir(deal_id) / "legal_results.json", [])

def load_financial_results(deal_id: str) -> List[Dict[str, Any]]:
    return _read_json(_deal_dir(deal_id) / "financial_results.json", [])

def already_processed(deal_id: str, filename: str) -> bool:
    fn = filename.strip()
    for r in load_legal_results(deal_id):
        if r.get("filename") == fn:
            return True
    for r in load_financial_results(deal_id):
        if r.get("filename") == fn:
            return True
    return False

def append_legal_result(deal_id: str, result: Dict[str, Any]) -> None:
    path = _deal_dir(deal_id) / "legal_results.json"
    arr: List[Dict[str, Any]] = _read_json(path, [])
    arr.append(result)
    _write_json(path, arr)

def append_financial_result(deal_id: str, result: Dict[str, Any]) -> None:
    path = _deal_dir(deal_id) / "financial_results.json"
    arr: List[Dict[str, Any]] = _read_json(path, [])
    arr.append(result)
    _write_json(path, arr)
