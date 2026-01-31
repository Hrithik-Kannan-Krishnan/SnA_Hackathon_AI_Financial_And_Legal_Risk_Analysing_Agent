from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Union

DEALS_PATH = Path("storage") / "sqlite" / "deals.json"
DEALS_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_deals() -> List[Dict[str, Any]]:
    if not DEALS_PATH.exists():
        return []
    try:
        return json.loads(DEALS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_deals(deals: List[Dict[str, Any]]) -> None:
    DEALS_PATH.write_text(json.dumps(deals, indent=2), encoding="utf-8")

def upsert_deal(*args, **kwargs) -> None:
    """
    Backward-compatible:
      upsert_deal(deal_id: str, deal_name: str)
      upsert_deal({"deal_id":..., "deal_name":...})
    """
    if len(args) == 1 and isinstance(args[0], dict):
        deal = args[0]
    elif len(args) == 2 and isinstance(args[0], str):
        deal = {"deal_id": args[0], "deal_name": args[1]}
    elif "deal_id" in kwargs and "deal_name" in kwargs:
        deal = {"deal_id": kwargs["deal_id"], "deal_name": kwargs["deal_name"]}
    else:
        raise TypeError("upsert_deal expects (deal_id, deal_name) or (deal_dict)")

    did = deal.get("deal_id")
    if not did:
        raise ValueError("deal_id is required")

    deals = load_deals()
    updated = False
    for i, d in enumerate(deals):
        if d.get("deal_id") == did:
            deals[i] = {**d, **deal}
            updated = True
            break
    if not updated:
        deals.append(deal)

    save_deals(deals)

# Aliases used in other pages
def save_deal(deal: Dict[str, Any]) -> None:
    upsert_deal(deal)

def save_deals_list(deals: List[Dict[str, Any]]) -> None:
    save_deals(deals)
