import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import extraction functions after setting up path
try:
    from src.extractors.pdf_text import extract_pdf_text
except ImportError:
    extract_pdf_text = None
try:
    from src.extractors.docx_text import extract_docx_text  
except ImportError:
    extract_docx_text = None
try:
    from src.extractors.pptx_text import extract_pptx_text
except ImportError:
    extract_pptx_text = None
from src.extractors.tabular_text import extract_csv_text, extract_xlsx_text

def extract_any_text(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        if extract_pdf_text is None:
            raise ValueError("PDF extraction not available - pypdf not installed")
        return extract_pdf_text(path)
    if ext == ".docx":
        if extract_docx_text is None:
            raise ValueError("DOCX extraction not available - python-docx not installed")
        return extract_docx_text(path)
    if ext == ".pptx":
        if extract_pptx_text is None:
            raise ValueError("PPTX extraction not available - python-pptx not installed")
        return extract_pptx_text(path)
    if ext == ".csv":
        return extract_csv_text(path)
    if ext == ".xlsx":
        return extract_xlsx_text(path)
    raise ValueError(f"Unsupported file type for analysis: {ext}")

import uuid
import streamlit as st
from src.ui.deal_selector import deal_selector

def render_flashcard(title, value, icon="", color_class="", details=None, progress_value=None):
    """Simple replacement for theme manager flashcard"""
    if icon:
        label = f"{icon} {title}"
    else:
        label = title
    
    delta_info = None
    if details:
        delta_info = ", ".join(str(d) for d in details[:2])
    elif progress_value is not None:
        delta_info = f"{progress_value}%"
    
    st.metric(label=label, value=str(value), delta=delta_info)

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

st.set_page_config(page_title="Red Flag AI", layout="wide")

settings = get_settings()

@st.cache_resource
def qdrant_client():
    return get_qdrant_local_client(settings.qdrant_path)


st.title("Red Flag AI")

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
    st.subheader("Upload and View Deals")

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
                
                # Display completeness analysis results with document-type-aware scoring
                if res.completeness:
                    comp = res.completeness
                    st.markdown(f"**📊 Legal Completeness Analysis for {d['original_name']}**")
                    
                    # Display scores with detailed breakdown
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            label="🪣 Bucket Score",
                            value=f"{comp.scores.bucket_coverage_score}/70",
                            delta=f"{int((comp.scores.bucket_coverage_score/70)*100)}%"
                        )
                    with col2:
                        st.metric(
                            label="🔍 Evidence Score",
                            value=f"{comp.scores.evidence_strength_score}/30",
                            delta=f"{int((comp.scores.evidence_strength_score/30)*100)}%"
                        )
                    with col3:
                        overall_score = comp.scores.overall_score
                        score_color = ("score-excellent" if overall_score >= 80 else 
                                      "score-good" if overall_score >= 60 else
                                      "score-warning" if overall_score >= 40 else "score-poor")
                        st.metric(
                            label="🎯 Overall Score",
                            value=f"{overall_score}/100",
                            delta=f"{overall_score}%"
                        )
                    with col4:
                        classification = comp.scores.classification.replace("_", " ").title()
                        class_icon = "✅" if classification == 'Accept Ok' else ("⚠️" if classification == 'Accept With Warnings' else "🚫")
                        class_color = ("score-excellent" if classification == 'Accept Ok' else 
                                      "score-warning" if classification == 'Accept With Warnings' else "score-poor")
                        st.metric(
                            label=f"{class_icon} Classification",
                            value=classification
                        )
                    
                    # Apply classification-based UI styling
                    if comp.scores.classification == "reject_incomplete":
                        st.error(f"🚫 **Document Rejected** (Score: {comp.scores.overall_score}/100)")
                        if "HARD_FAIL" in str(comp.flags.missing_core_buckets):
                            st.error(f"**Hard Fail Rule Triggered**: {comp.flags.missing_core_buckets[0]}")
                        else:
                            st.warning("📋 **Message**: Document lacks core deal/legal/financial sections. Upload definitive agreement / schedules / financials.")
                        st.warning(f"Missing core buckets: {', '.join([b for b in comp.flags.missing_core_buckets if not b.startswith('HARD_FAIL')])}")
                    
                    elif comp.scores.classification == "accept_with_warnings":
                        st.warning(f"⚠️ **Accepted with Warnings** (Score: {comp.scores.overall_score}/100)")
                        st.info("📋 **Message**: Partial document; risks may be missed.")
                        if comp.flags.missing_core_buckets:
                            st.caption(f"Missing buckets: {', '.join(comp.flags.missing_core_buckets)}")
                    
                    else:  # accept_ok
                        st.success(f"✅ **Document Accepted** (Score: {comp.scores.overall_score}/100)")
                        st.info("📋 **Message**: Proceed normally.")
                    
                    # Show additional flags
                    if comp.flags.likely_teaser_or_summary:
                        st.warning("🏷️ **Likely teaser/LOI detected** - forced to 'accept_with_warnings' at best")
                    if comp.flags.generic_language_without_details:
                        st.warning("📝 Generic language without specific details detected")
                    if comp.flags.unsupported_no_litigation_claim:
                        st.warning("⚖️ Unsupported 'no litigation' claim without schedule references")
                    
                    # Show evidence strength breakdown
                    with st.expander("Evidence Strength Details"):
                        evidence_details = []
                        if comp.evidence_strength.numbers_present or comp.price_and_payment.currency_present:
                            evidence_details.append("✅ Currency/Numbers (+6 pts)")
                        if comp.evidence_strength.dates_present:
                            evidence_details.append("✅ Dates Present (+6 pts)")
                        if comp.evidence_strength.percentages_present:
                            evidence_details.append("✅ Percentages (+4 pts)")
                        if comp.evidence_strength.defined_term_pattern_present:
                            evidence_details.append("✅ Defined Terms (+7 pts)")
                        if comp.evidence_strength.schedule_exhibit_pattern_present:
                            evidence_details.append("✅ Schedules/Exhibits (+7 pts)")
                        
                        if evidence_details:
                            for detail in evidence_details:
                                st.write(detail)
                        else:
                            st.write("❌ No strong evidence indicators found")
                
                elif res.financial_completeness:
                    fcomp = res.financial_completeness
                    st.markdown(f"**📊 Financial Completeness Analysis for {d['original_name']}**")
                    
                    # Display financial scores with detailed breakdown
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Statements Score", f"{fcomp.scores.financial_statements_score}/30")
                    with col2:
                        st.metric("Performance Score", f"{fcomp.scores.performance_metrics_score}/25")
                    with col3:
                        st.metric("Period Score", f"{fcomp.scores.period_evidence_score}/25")
                    with col4:
                        st.metric("Numeric Score", f"{fcomp.scores.numeric_content_score}/20")
                    
                    # Overall score and classification
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Overall Score", f"{fcomp.scores.overall_score}/100")
                    with col2:
                        st.metric("Classification", fcomp.scores.classification.replace("_", " ").title())
                    
                    # Apply classification-based UI styling for financial documents
                    if fcomp.scores.classification == "reject_incomplete":
                        st.error(f"🚫 **Financial Document Rejected** (Score: {fcomp.scores.overall_score}/100)")
                        if fcomp.flags.no_financial_statements:
                            st.error("**Missing Financial Statements**: No P&L, Balance Sheet, or Cash Flow found")
                        if fcomp.flags.insufficient_performance_metrics:
                            st.error("**Insufficient Performance Metrics**: Need at least 2 metrics (Sales, Expenses, Profit, EPS, EBITDA)")
                        if fcomp.flags.missing_period_evidence:
                            st.error("**Missing Period Evidence**: No FY dates, quarters, or year references found")
                        if fcomp.flags.minimal_numeric_content:
                            st.warning("**Minimal Numeric Content**: Insufficient financial data")
                        st.warning("📋 **Message**: Upload complete financial statements with performance data and period information.")
                    
                    elif fcomp.scores.classification == "accept_with_warnings":
                        st.warning(f"⚠️ **Financial Document Accepted with Warnings** (Score: {fcomp.scores.overall_score}/100)")
                        st.info("📋 **Message**: Partial financial data; some analysis may be limited.")
                        
                        warnings = []
                        if fcomp.flags.insufficient_performance_metrics:
                            warnings.append("Limited performance metrics")
                        if fcomp.flags.missing_period_evidence:
                            warnings.append("Missing period information")
                        if warnings:
                            st.caption(f"Warnings: {', '.join(warnings)}")
                    
                    else:  # accept_ok
                        st.success(f"✅ **Financial Document Accepted** (Score: {fcomp.scores.overall_score}/100)")
                        st.info("📋 **Message**: Complete financial data - proceed with analysis.")
                    
                    # Show financial statement details
                    with st.expander("Financial Statements Found"):
                        statements = []
                        if fcomp.financial_statements.profit_and_loss_present:
                            statements.append("✅ Profit & Loss Statement")
                        if fcomp.financial_statements.balance_sheet_present:
                            statements.append("✅ Balance Sheet")
                        if fcomp.financial_statements.cash_flow_present:
                            statements.append("✅ Cash Flow Statement")
                        if fcomp.financial_statements.notes_present:
                            statements.append("✅ Notes to Financial Statements")
                        
                        if statements:
                            for stmt in statements:
                                st.write(stmt)
                        else:
                            st.write("❌ No financial statement patterns found")
                    
                    # Show performance metrics details
                    with st.expander("Performance Metrics Found"):
                        metrics = []
                        if fcomp.performance_metrics.sales_revenue_present:
                            metrics.append("✅ Sales/Revenue")
                        if fcomp.performance_metrics.expenses_present:
                            metrics.append("✅ Expenses")
                        if fcomp.performance_metrics.net_profit_present:
                            metrics.append("✅ Net Profit")
                        if fcomp.performance_metrics.eps_present:
                            metrics.append("✅ Earnings Per Share")
                        if fcomp.performance_metrics.ebitda_present:
                            metrics.append("✅ EBITDA/Operating Profit")
                        
                        if metrics:
                            for metric in metrics:
                                st.write(metric)
                        else:
                            st.write("❌ No performance metrics found")
                    
                    # Show period evidence
                    with st.expander("Period Evidence Found"):
                        periods = []
                        if fcomp.period_evidence.fy_ending_present:
                            periods.append("✅ Financial Year Ending dates")
                        if fcomp.period_evidence.quarterly_dates_present:
                            periods.append("✅ Quarterly periods")
                        if fcomp.period_evidence.monthly_periods_present:
                            periods.append("✅ Monthly periods")
                        if fcomp.period_evidence.year_references_present:
                            periods.append("✅ Year references")
                        
                        if periods:
                            for period in periods:
                                st.write(period)
                        else:
                            st.write("❌ No clear period evidence found")
                
                upsert_doc(deal_id, {
                    "doc_id": d["doc_id"],
                    "filename": d["original_name"],
                    "stored_path": d["stored_path"],
                    "doc_type": res.router.doc_type,
                    "router_rationale": res.router.rationale,
                })


                if res.legal is not None:
                    result_data = {
                        "doc_id": d["doc_id"],
                        "filename": d["original_name"],
                        "router": res.router.model_dump(),
                        "legal": res.legal.model_dump(),
                    }
                    # Include completeness data if available (legal documents)
                    if res.completeness:
                        result_data["completeness"] = res.completeness.model_dump()
                    # Include financial completeness data if available
                    if res.financial_completeness:
                        result_data["financial_completeness"] = res.financial_completeness.model_dump()
                    
                    append_legal_result(deal_id, result_data)
                    st.success(f"Saved Legal result: {d['original_name']}")

                elif res.financial is not None:
                    result_data = {
                        "doc_id": d["doc_id"],
                        "filename": d["original_name"],
                        "router": res.router.model_dump(),
                        "financial": res.financial.model_dump(),
                    }
                    # Include completeness data if available (legal documents)
                    if res.completeness:
                        result_data["completeness"] = res.completeness.model_dump()
                    # Include financial completeness data if available (financial documents)
                    if res.financial_completeness:
                        result_data["financial_completeness"] = res.financial_completeness.model_dump()
                    
                    append_financial_result(deal_id, result_data)
                    st.success(f"Saved Financial result: {d['original_name']}")

                else:
                    st.info(f"Router classified as '{res.router.doc_type}': no agent run for {d['original_name']}")
                    # Still save completeness analysis even if no agent was run
                    if res.completeness and res.completeness.scores.classification == "reject_incomplete":
                        st.error(f"Legal document rejected due to insufficient completeness: {res.router.rationale}")
                    if res.financial_completeness and res.financial_completeness.scores.classification == "reject_incomplete":
                        st.error(f"Financial document rejected due to insufficient completeness: {res.router.rationale}")


        try:
            collections = [c.name for c in qdrant_client().get_collections().collections]
            if COLLECTION_NAME in collections:
                cnt = qdrant_client().count(collection_name=COLLECTION_NAME, exact=True).count
                st.caption(f"Qdrant collection `{COLLECTION_NAME}` now has **{cnt}** points (chunks).")
        except Exception:
            pass

st.divider()
