from __future__ import annotations
import streamlit as st
from src.db.deals_store import load_deals

def deal_selector(key: str = "deal_select") -> tuple[str, str]:
    """
    Returns (deal_id, deal_name) and stores in st.session_state.selected_deal_id/name.
    """
    deals = load_deals()
    if not deals:
        st.warning("No deals yet. Create one on Home.")
        st.stop()

    labels = [f"{d['deal_name']} ({d['deal_id']})" for d in deals]
    label_to = {labels[i]: deals[i] for i in range(len(deals))}

    default_ix = 0
    last = st.session_state.get("selected_deal_id")
    if last:
        for i, d in enumerate(deals):
            if d["deal_id"] == last:
                default_ix = i
                break

    chosen = st.selectbox("Select deal", labels, index=default_ix, key=key)
    deal = label_to[chosen]
    st.session_state["selected_deal_id"] = deal["deal_id"]
    st.session_state["selected_deal_name"] = deal["deal_name"]
    return deal["deal_id"], deal["deal_name"]
