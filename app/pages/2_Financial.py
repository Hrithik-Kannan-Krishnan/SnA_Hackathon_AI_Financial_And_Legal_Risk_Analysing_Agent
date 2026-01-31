import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.ui.deal_selector import deal_selector
from src.db.results_store import load_financial_results

st.set_page_config(page_title="Financial", layout="wide")

st.title("Financial")
deal_id, deal_name = deal_selector(key="fin_deal")
st.caption(f"Deal: **{deal_name}** (`{deal_id}`)")

rows = load_financial_results(deal_id)
st.write(f"Found **{len(rows)}** financial analyses.")

for r in rows[::-1]:
    fin = r.get("financial", {})
    anomalies = fin.get("anomalies", [])
    with st.expander(f"{r.get('filename')}  —  Anomalies: {len(anomalies)}"):
        st.write("**Key metrics mentioned**")
        st.write(fin.get("key_metrics", []))
        st.write("**Anomalies**")
        st.write(anomalies)
        st.write("**Rationale**")
        st.write(fin.get("rationale", ""))
