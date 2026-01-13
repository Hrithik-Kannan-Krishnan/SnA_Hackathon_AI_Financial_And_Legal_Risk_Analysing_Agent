import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.ui.deal_selector import deal_selector
from src.db.results_store import load_legal_results, load_financial_results
from src.db.doc_index import load_doc_index
from src.storage.docs_index import list_docs_for_deal
from src.core.risk_scoring import overall_risk_level
from src.llm.ollama_chat import ollama_chat
from src.core.settings import get_settings

st.set_page_config(page_title="Deal Overview", layout="wide")

settings = get_settings()
st.title("Deal Overview (Dashboard)")

deal_id, deal_name = deal_selector(key="overview_deal")
st.caption(f"Deal: **{deal_name}** (`{deal_id}`)")

legal_rows = load_legal_results(deal_id)
fin_rows = load_financial_results(deal_id)

# Counts
high_contracts = sum(1 for r in legal_rows if r.get("legal", {}).get("risk_level") == "High")
med_contracts = sum(1 for r in legal_rows if r.get("legal", {}).get("risk_level") == "Medium")
fin_anoms = sum(len(r.get("financial", {}).get("anomalies", []) or []) for r in fin_rows)

risk = overall_risk_level(legal_rows, fin_rows)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Overall risk", risk)
c2.metric("High-risk contracts", high_contracts)
c3.metric("Financial anomalies", fin_anoms)
docs = list_docs_for_deal(deal_id)
doc_index = load_doc_index(deal_id)
c4.metric("Docs uploaded", len(docs))

st.divider()
c5, c6, c7 = st.columns(3)
c5.metric('Indexed (routed)', len(doc_index))
c6.metric('Legal analyzed', len(legal_rows))
c7.metric('Financial analyzed', len(fin_rows))



# Headlines generated from stored outputs (grounded)
st.subheader("Key insights (LLM headlines)")

if st.button("Generate headlines (3–5)"):
    # Build compact context from existing results
    bullets = []
    for r in legal_rows[:10]:
        legal = r.get("legal", {})
        lvl = legal.get("risk_level")
        reds = legal.get("red_flags", [])
        if reds:
            bullets.append(f"LEGAL {lvl} — {r.get('filename')}: red_flags={reds[:4]}")
        else:
            bullets.append(f"LEGAL {lvl} — {r.get('filename')}: no explicit red_flags extracted")

    for r in fin_rows[:10]:
        fin = r.get("financial", {})
        an = fin.get("anomalies", [])
        if an:
            bullets.append(f"FIN — {r.get('filename')}: anomalies={an[:4]}")
        else:
            bullets.append(f"FIN — {r.get('filename')}: no anomalies extracted")

    context = "\n".join(bullets) if bullets else "No stored analyses yet."

    system = (
        "You are a due diligence copilot.\n"
        "Create 3 to 5 concise headlines ONLY from the provided context.\n"
        "Do not invent facts. If context is thin, say so.\n"
    )
    user = f"CONTEXT:\n{context}\n\nTASK:\nWrite 3-5 bullet headlines."

    out = ollama_chat(
        base_url=settings.ollama_base_url,
        model=settings.chat_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    st.write(out)

st.divider()
c5, c6, c7 = st.columns(3)
c5.metric('Indexed (routed)', len(doc_index))
c6.metric('Legal analyzed', len(legal_rows))
c7.metric('Financial analyzed', len(fin_rows))

