import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from src.ui.deal_selector import deal_selector
from src.core.settings import get_settings
from src.vectordb.qdrant_store import get_qdrant_local_client
from src.embeddings.ollama_embed import embed_text
from src.rag.retriever import retrieve_chunks
from src.rag.answer_with_citations import build_context, SYSTEM_CITED, format_sources
from src.llm.ollama_chat import ollama_chat

st.set_page_config(page_title="Copilot Chat", layout="wide")
st.title("Copilot Chat")

settings = get_settings()
deal_id, deal_name = deal_selector(key="chat_deal")

# Clear chat automatically when deal changes
if st.session_state.get("_last_chat_deal_id") != deal_id:
    st.session_state["_last_chat_deal_id"] = deal_id
    st.session_state["chat"] = []

st.caption(f"Deal: **{deal_name}** (`{deal_id}`)")

colA, colB = st.columns([1, 1])
with colA:
    if st.button("Clear chat"):
        st.session_state["chat"] = []
        st.rerun()
with colB:
    st.caption("Chat answers are grounded in Qdrant RAG sources only.")

@st.cache_resource
def qdrant_client():
    return get_qdrant_local_client(settings.qdrant_path)

client = qdrant_client()

if "chat" not in st.session_state:
    st.session_state.chat = []

# Render history
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask about risks, change-of-control, anomalies, summaries...")
if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Retrieve
    qvec = embed_text(settings.ollama_base_url, settings.embed_model, prompt)
    chunks = retrieve_chunks(client, deal_id=deal_id, query_vector=qvec, top_k=6)

    if not chunks:
        answer = "I couldn’t find relevant content in the indexed documents for this deal."
        st.session_state.chat.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.stop()

    context = build_context(chunks)
    user_msg = f"SOURCES:\n{context}\n\nQUESTION:\n{prompt}"

    answer = ollama_chat(
        base_url=settings.ollama_base_url,
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_CITED},
            {"role": "user", "content": user_msg},
        ],
    )

    with st.chat_message("assistant"):
        st.markdown(answer)
        with st.expander("Sources used (top retrieved chunks)"):
            st.code(format_sources(chunks), language="text")
            st.divider()
            for i, c in enumerate(chunks, start=1):
                st.markdown(f"**[S{i}] {c.get('filename')} (chunk {c.get('chunk_id')})**")
                st.write((c.get("text","") or "")[:600] + ("..." if len((c.get("text","") or "")) > 600 else ""))

    st.session_state.chat.append({"role": "assistant", "content": answer})
