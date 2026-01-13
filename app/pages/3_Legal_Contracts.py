import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.ui.deal_selector import deal_selector
from src.db.results_store import load_legal_results

st.set_page_config(page_title="Legal & Contracts", layout="wide")
st.title("Legal & Contracts")

deal_id, deal_name = deal_selector(key="legal_deal")
st.caption(f"Deal: **{deal_name}** (`{deal_id}`)")

rows = load_legal_results(deal_id)

# Sort High -> Medium -> Low
rank = {"High": 0, "Medium": 1, "Low": 2}
rows_sorted = sorted(rows, key=lambda r: rank.get(r.get("legal", {}).get("risk_level", "Low"), 9))

st.write(f"Found **{len(rows_sorted)}** legal analyses (sorted by risk).")

for r in rows_sorted:
    legal = r.get("legal", {})
    lvl = legal.get("risk_level", "Low")
    reds = legal.get("red_flags", []) or []
    evid = legal.get("evidence", []) or []

    badge = "🟥 High" if lvl == "High" else "🟧 Medium" if lvl == "Medium" else "🟩 Low"
    title = f"{badge} — {r.get('filename')}"

    with st.expander(title, expanded=(lvl in ("High","Medium"))):
        if reds:
            st.markdown("### Red flags")
            for rf in reds:
                st.warning(rf)
        else:
            st.info("No explicit red flags extracted.")

        if evid:
            st.markdown("### Evidence")
            for e in evid:
                st.markdown(f"**{e.get('label','evidence')}**")
                st.code(e.get("snippet",""), language="text")
                st.caption(e.get("note",""))
        else:
            st.caption("No evidence snippets provided.")

        st.markdown("### Clauses / headings")
        st.write(legal.get("clauses", []))

        st.markdown("### Rationale")
        st.write(legal.get("rationale",""))
