import sys
from pathlib import Path

def extract_any_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return extract_pdf_text(path)
    if ext == ".docx":
        return extract_docx_text(path)
    if ext == ".pptx":
        return extract_pptx_text(path)
    if ext == ".csv":
        return extract_csv_text(path)
    if ext == ".xlsx":
        return extract_xlsx_text(path)
    raise ValueError(f"Unsupported file type for analysis: {ext}")


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uuid
import streamlit as st
from src.ui.deal_selector import deal_selector

from src.core.settings import get_settings
from src.llm.ollama_client import ollama_healthcheck
from src.vectordb.qdrant_store import qdrant_healthcheck, get_qdrant_local_client
from src.ingestion.validators import validate_filename, validate_size, ALLOWED_EXTENSIONS
from src.storage.blob_store import save_upload_bytes
from src.ingestion.ingest_rag import ingest_file_to_qdrant, COLLECTION_NAME
from src.agents.crew_runner import run_pipeline
from src.db.results_store import append_legal_result, append_financial_result
from src.db.deals_store import load_deals
from src.db.results_store import already_processed
from src.db.doc_index import upsert_doc
from src.storage.blobs_scan import list_deal_files
from src.storage.zip_unpack import unpack_zip
from src.ingestion.ingest_rag import ingest_file_to_qdrant
from src.db.deals_store import upsert_deal

st.set_page_config(page_title="DealRoom Copilot (MVP)", layout="wide")
settings = get_settings()

@st.cache_resource
def qdrant_client():
    return get_qdrant_local_client(settings.qdrant_path)


# ✅ Create ONE Qdrant client for the whole app run
st.title("DealRoom Copilot (MVP)")
st.caption("Step 3.1: PDF -> chunks -> embeddings -> Qdrant (RAG index)")

# ---- Deal selector (global) ----
_deals = load_deals()
if _deals:
    deal_id, deal_name = deal_selector(key="home_deal")
    st.caption(f"Selected deal: **{deal_name}** (`{deal_id}`)")
else:
    st.info("No deals yet — create one below to enable uploads and analysis.")

with st.sidebar:
    st.header("System Status")
    ok_ollama, msg_ollama = ollama_healthcheck(settings.ollama_base_url)
    ok_qdrant, msg_qdrant = qdrant_healthcheck(settings.qdrant_path)

    st.write("**Ollama**:", "✅" if ok_ollama else "❌")
    st.caption(msg_ollama)
    st.write("**Qdrant (local)**:", "✅" if ok_qdrant else "❌")
    st.caption(msg_qdrant)

    st.divider()
    st.write("**Config**")
    st.code(
        f"OLLAMA_BASE_URL={settings.ollama_base_url}\n"
        f"QDRANT_PATH={settings.qdrant_path}\n"
        f"SQLITE_PATH={settings.sqlite_path}\n"
        f"EMBED_MODEL={settings.embed_model}\n",
        language="text",
    )

    embed_model = st.text_input("Embedding model (Ollama)", value=settings.embed_model)
    st.session_state["EMBED_MODEL"] = embed_model

if "deals" not in st.session_state:
    st.session_state.deals = []
if "selected_deal_id" not in st.session_state:
    st.session_state.selected_deal_id = None
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []

colA, colB = st.columns([2, 1], gap="large")

with colA:
    st.subheader("Screen 1: Deal list + Upload + RAG ingest")

    with st.form("create_deal", clear_on_submit=True):
        deal_name = st.text_input("Deal name", placeholder="e.g., Reliance–Disney Dataroom Demo")
        submitted = st.form_submit_button("Create deal")
        if submitted:
            if not deal_name.strip():
                st.error("Please enter a deal name.")
            else:
                deal_id = str(uuid.uuid4())[:8]
                st.session_state.deals.append({"deal_id": deal_id, "deal_name": deal_name.strip()})
                upsert_deal(deal_id, deal_name.strip())
                st.session_state.selected_deal_id = deal_id
                st.success(f"Deal created: {deal_name.strip()} ({deal_id})")

    if st.session_state.deals:
        options = {f"{d['deal_name']} ({d['deal_id']})": d["deal_id"] for d in st.session_state.deals}
        labels = list(options.keys())
        default_ix = 0
        if st.session_state.selected_deal_id:
            for i, label in enumerate(labels):
                if options[label] == st.session_state.selected_deal_id:
                    default_ix = i
                    break

        selected_label = st.selectbox("Select a deal", labels, index=default_ix)
        st.session_state.selected_deal_id = options[selected_label]
        st.caption(f"Selected deal_id: `{st.session_state.selected_deal_id}`")
    else:
        st.info("Create a deal to enable uploads.")

    st.divider()

    if st.session_state.deals and st.session_state.selected_deal_id:
        st.markdown("#### Upload documents (drag & drop)")
        st.caption(f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        MAX_MB = 50
        max_bytes = MAX_MB * 1024 * 1024

        files = st.file_uploader(
            "Upload files",
            type=["pdf","docx","pptx","xlsx","csv","zip"],
            accept_multiple_files=True,
        )

        if files:
            if st.button("Save uploads to storage"):
                saved = 0
                for f in files:
                    name_res = validate_filename(f.name)
                    if not name_res.ok:
                        st.error(f"{f.name}: {name_res.reason}")
                        continue

                    content = f.getvalue()
                    size_res = validate_size(len(content), max_bytes=max_bytes)
                    if not size_res.ok:
                        st.error(f"{f.name}: {size_res.reason}")
                        continue

                    stored = save_upload_bytes(
                        root=Path("storage"),
                        deal_id=st.session_state.selected_deal_id,
                        original_name=f.name,
                        content=content,
                    )
                    st.session_state.uploaded_docs.append(
                        {
                            "doc_id": stored.doc_id,
                            "deal_id": stored.deal_id,
                            "original_name": stored.original_name,
                            "stored_path": str(stored.stored_path),
                            "size_bytes": stored.size_bytes,
                        }
                    )
                    saved += 1
                st.success(f"Saved {saved} file(s) to storage/blobs/")

    if st.session_state.uploaded_docs:
        st.markdown("#### Documents queued (saved to blob storage)")
        for d in st.session_state.uploaded_docs[::-1]:
            st.write(
                f"• `{d['doc_id']}` — **{d['original_name']}** "
                f"({d['size_bytes']/1024:.1f} KB)  \n"
                f"  ↳ `{d['stored_path']}`"
            )

        st.divider()
        st.markdown("### Step 3.1: Ingest queued PDFs into RAG (Qdrant)")

        if st.button("Ingest queued docs into RAG"):
            embed_model = st.session_state.get("EMBED_MODEL", settings.embed_model)
            total_chunks = 0
            for d in st.session_state.uploaded_docs:
                res = ingest_file_to_qdrant(
                    client=qdrant_client(),
                    deal_id=d["deal_id"],
                    doc_id=d["doc_id"],
                    filename=d["original_name"],
                    stored_path=d["stored_path"],
                    ollama_base_url=settings.ollama_base_url,
                    embed_model=embed_model,
                    qdrant_path=settings.qdrant_path,
                )
                total_chunks += res.chunks_ingested
                st.success(f"Ingested {d['original_name']} → {res.chunks_ingested} chunks")
                if res.chunks_ingested == 0:
                    st.warning("No text extracted (possibly scanned PDF without OCR, or empty file).")
                else:
                    st.caption("Indexed into Qdrant for RAG search.")

                # "{d['original_name']}: {res['reason']}")

            st.info(f"Total chunks ingested this run: {total_chunks}")

        st.markdown("### Step 4.2: Run Router + Agents on queued docs (Legal/Financial)")
        st.caption("This stores outputs to storage/results/<deal_id>/ for dashboard tabs.")

        if st.button("Run Router + Agents (CrewAI)"):
            deal_id = st.session_state.get("selected_deal_id", "")
            if not deal_id:
                st.error("Select/create a deal first.")
                st.stop()

            docs = list_deal_files(deal_id)
            st.write(f"Found **{len(docs)}** PDF(s) in blob storage for this deal.")

            if not docs:
                st.warning("No PDFs found under storage/blobs for this deal. Upload PDFs first.")
                st.stop()

            for d in docs:
                if already_processed(deal_id, d["original_name"]):
                    st.info(f"Skipping already processed: {d['original_name']}")
                    continue

                from src.extractors.pdf_text import extract_pdf_text
                from src.extractors.docx_text import extract_docx_text
                from src.extractors.pptx_text import extract_pptx_text
                from src.extractors.tabular_text import extract_csv_text, extract_xlsx_text
                text = extract_any_text(d["stored_path"])
                if not text.strip():
                    st.error(f"No text extracted (OCR step later): {d['original_name']}")
                    continue

                with st.spinner(f"Running CrewAI on: {d['original_name']}"):
                    res = run_pipeline(d["original_name"], text)
                upsert_doc(deal_id, {
                    "doc_id": d["doc_id"],
                    "filename": d["original_name"],
                    "stored_path": d["stored_path"],
                    "doc_type": res.router.doc_type,
                    "router_rationale": res.router.rationale,
                })


                if res.legal is not None:
                    append_legal_result(
                        deal_id,
                        {
                            "doc_id": d["doc_id"],
                            "filename": d["original_name"],
                            "router": res.router.model_dump(),
                            "legal": res.legal.model_dump(),
                        },
                    )
                    st.success(f"Saved Legal result: {d['original_name']}")

                elif res.financial is not None:
                    append_financial_result(
                        deal_id,
                        {
                            "doc_id": d["doc_id"],
                            "filename": d["original_name"],
                            "router": res.router.model_dump(),
                            "financial": res.financial.model_dump(),
                        },
                    )
                    st.success(f"Saved Financial result: {d['original_name']}")

                else:
                    st.info(f"Router classified as '{res.router.doc_type}': no agent run for {d['original_name']}")


        try:
            collections = [c.name for c in qdrant_client().get_collections().collections]
            if COLLECTION_NAME in collections:
                cnt = qdrant_client().count(collection_name=COLLECTION_NAME, exact=True).count
                st.caption(f"Qdrant collection `{COLLECTION_NAME}` now has **{cnt}** points (chunks).")
        except Exception:
            pass

st.divider()
