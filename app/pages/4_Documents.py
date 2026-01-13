import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.ui.deal_selector import deal_selector
from src.storage.docs_index import list_docs_for_deal
from src.db.results_store import load_legal_results, load_financial_results
from src.db.doc_index import load_doc_index

st.set_page_config(page_title="Documents", layout="wide")
st.title("Documents")

deal_id, deal_name = deal_selector(key="docs_deal")
st.caption(f"Deal: **{deal_name}** (`{deal_id}`)")

docs = list_docs_for_deal(deal_id)
doc_index = load_doc_index(deal_id)
legal = load_legal_results(deal_id)
fin = load_financial_results(deal_id)

idx_by_file = {d["filename"]: d for d in doc_index}
legal_by_file = {r.get("filename"): r for r in legal}
fin_by_file = {r.get("filename"): r for r in fin}

st.write(f"Uploaded: **{len(docs)}** | Routed: **{len(doc_index)}** | Legal analyzed: **{len(legal)}** | Financial analyzed: **{len(fin)}**")
st.divider()

if not docs:
    st.info("No documents found for this deal.")
    st.stop()

for d in docs:
    fn = d["filename"]
    routed = idx_by_file.get(fn, {})
    doc_type = routed.get("doc_type", "unknown")
    analyzed = "Legal" if fn in legal_by_file else "Financial" if fn in fin_by_file else "Not analyzed"
    status = f"Routed: {doc_type} | Analyzed: {analyzed}"

    with st.expander(f"{fn}  —  {status}  —  {d['size_kb']} KB"):
        st.code(d["path"], language="text")
        if routed:
            st.write("Router rationale:", routed.get("router_rationale", ""))
