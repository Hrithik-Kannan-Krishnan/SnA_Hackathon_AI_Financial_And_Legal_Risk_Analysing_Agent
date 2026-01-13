from __future__ import annotations
from typing import List, Dict, Any

def overall_risk_level(legal_rows: List[Dict[str, Any]], fin_rows: List[Dict[str, Any]]) -> str:
    """
    MVP heuristic:
    - Any High legal risk => High
    - Else if >=2 Medium legal OR >=3 anomalies across financial => Medium
    - Else Low
    """
    legal_levels = [r.get("legal", {}).get("risk_level") for r in legal_rows]
    if "High" in legal_levels:
        return "High"
    med_count = sum(1 for x in legal_levels if x == "Medium")
    fin_anoms = sum(len(r.get("financial", {}).get("anomalies", []) or []) for r in fin_rows)
    if med_count >= 2 or fin_anoms >= 3:
        return "Medium"
    return "Low"
