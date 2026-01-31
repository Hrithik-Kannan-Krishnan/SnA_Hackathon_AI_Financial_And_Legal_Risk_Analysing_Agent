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

def render_flashcard(title, value, icon="", color_class="", details=None, progress_value=None):
    """Simple replacement for theme manager flashcard"""
    # Extract icon from title if present
    if icon:
        label = f"{icon} {title}"
    else:
        label = title
    
    # Create delta info
    delta_info = None
    if details:
        delta_info = ", ".join(str(d) for d in details[:2])  # Limit to first 2 items
    elif progress_value is not None:
        delta_info = f"{progress_value}%"
    
    st.metric(label=label, value=str(value), delta=delta_info)

st.set_page_config(page_title="Deal Overview", layout="wide")

settings = get_settings()
st.title("Deal Overview Dashboard")

deal_id, deal_name = deal_selector(key="overview_deal")
st.caption(f"Deal: **{deal_name}** (`{deal_id}`)")

legal_rows = load_legal_results(deal_id)
fin_rows = load_financial_results(deal_id)

# Counts
high_contracts = sum(1 for r in legal_rows if r.get("legal", {}).get("risk_level") == "High")
med_contracts = sum(1 for r in legal_rows if r.get("legal", {}).get("risk_level") == "Medium")
fin_anoms = sum(len(r.get("financial", {}).get("anomalies", []) or []) for r in fin_rows)

# Extract completeness data
legal_completeness = [r for r in legal_rows if r.get("completeness")]
financial_completeness = [r for r in fin_rows if r.get("financial_completeness")]

risk = overall_risk_level(legal_rows, fin_rows)
docs = list_docs_for_deal(deal_id)
doc_index = load_doc_index(deal_id)

# Main metrics with flashcards
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

# Risk level flashcard
with col1:
    risk_color = "🔴" if risk == "High" else ("🟡" if risk == "Medium" else "🟢")
    st.metric(
        label="Overall Risk",
        value=risk,
        delta=risk_color
    )

# High-risk contracts flashcard
with col2:
    delta_icon = "🚨" if high_contracts > 0 else "✅"
    st.metric(
        label="High-Risk Contracts",
        value=str(high_contracts),
        delta=delta_icon
    )

# Financial anomalies flashcard
with col3:
    render_flashcard(
        title="Financial Anomalies", 
        value=str(fin_anoms),
        color_class="risk-high" if fin_anoms > 0 else "score-excellent"
    )

# Documents uploaded flashcard
with col4:
    render_flashcard(
        title="Documents Uploaded",
        value=str(len(docs)),
        color_class="score-good"
    )

st.divider()

# Processing stats with flashcards
st.subheader("Processing Statistics")
col5, col6, col7 = st.columns(3)

with col5:
    render_flashcard(
        title="Documents Indexed",
        value=str(len(doc_index)),
        color_class="score-good"
    )

with col6:
    render_flashcard(
        title="Legal Documents Analyzed",
        value=str(len(legal_rows)),
        color_class="score-good"
    )

with col7:
    render_flashcard(
        title="Financial Documents Analyzed",
        value=str(len(fin_rows)),
        color_class="score-good"
    )

st.divider()

# Completeness Analysis Section with enhanced flashcard UI
if legal_completeness or financial_completeness:
    st.subheader("Document Completeness Analysis")
    
    # Legal Document Completeness
    if legal_completeness:
        st.markdown("### Legal Documents Completeness")
        for result in legal_completeness:
            comp = result.get("completeness", {})
            scores = comp.get("scores", {})
            flags = comp.get("flags", {})
            filename = result.get("filename", "Unknown")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                overall_score = scores.get('overall_score', 0)
                score_color = ("score-excellent" if overall_score >= 80 else 
                              "score-good" if overall_score >= 60 else
                              "score-warning" if overall_score >= 40 else "score-poor")
                render_flashcard(
                    title=f"{filename[:20]}{'...' if len(filename) > 20 else ''}",
                    value=f"{overall_score}/100",
                    color_class=score_color,
                    progress_value=overall_score
                )
                
            with col2:
                classification = scores.get('classification', 'unknown').replace('_', ' ').title()
                class_color = ("score-excellent" if classification == 'Accept Ok' else 
                              "score-warning" if classification == 'Accept With Warnings' else "score-poor")
                render_flashcard(
                    title="Classification",
                    value=classification,
                    color_class=class_color
                )
                
            with col3:
                bucket_score = scores.get('bucket_coverage_score', 0)
                render_flashcard(
                    title="Bucket Coverage",
                    value=f"{bucket_score}/70",
                    progress_value=int((bucket_score/70)*100) if bucket_score > 0 else 0
                )
                
            with col4:
                evidence_score = scores.get('evidence_strength_score', 0)
                render_flashcard(
                    title="Evidence Strength", 
                    value=f"{evidence_score}/30",
                    progress_value=int((evidence_score/30)*100) if evidence_score > 0 else 0
                )
            
            # Show warnings and red flags for documents with warnings/rejections
            if classification in ['Accept With Warnings', 'Reject Incomplete']:
                with st.expander(f"⚠️ Issues for {filename}", expanded=False):
                    warnings = []
                    
                    # Missing core buckets
                    missing_buckets = flags.get('missing_core_buckets', [])
                    if missing_buckets:
                        # Filter out HARD_FAIL messages for display
                        clean_buckets = [b for b in missing_buckets if not b.startswith('HARD_FAIL')]
                        if clean_buckets:
                            warnings.append(f"**Missing Core Sections**: {', '.join(clean_buckets)}")
                    
                    # Specific flags
                    if flags.get('likely_teaser_or_summary'):
                        warnings.append("**⚠️ Likely Teaser/Summary**: Document appears to be a summary rather than complete agreement")
                    
                    if flags.get('generic_language_without_details'):
                        warnings.append("**⚠️ Generic Language**: Contains generic language without specific deal details")
                    
                    if flags.get('unsupported_no_litigation_claim'):
                        warnings.append("**⚠️ Unsupported Claims**: Contains 'no litigation' claims without proper schedule references")
                    
                    # Add legal analysis red flags if available
                    legal_data = result.get("legal", {})
                    red_flags = legal_data.get("red_flags", [])
                    if red_flags:
                        warnings.append(f"**🚨 Legal Red Flags**: {'; '.join(red_flags[:3])}")
                    
                    if warnings:
                        for warning in warnings:
                            st.markdown(f"- {warning}")
                    else:
                        st.markdown("- No specific warnings identified")
                    
                    # Show recommendation
                    if classification == 'Reject Incomplete':
                        st.error("📋 **Recommendation**: Upload complete definitive agreement with schedules and detailed terms")
                    else:
                        st.info("📋 **Recommendation**: Review highlighted sections for potential risks or missing information")
    
    # Financial Document Completeness with flashcard UI
    if financial_completeness:
        st.markdown("### Financial Documents Completeness")
        for result in financial_completeness:
            fcomp = result.get("financial_completeness", {})
            scores = fcomp.get("scores", {})
            flags = fcomp.get("flags", {})
            filename = result.get("filename", "Unknown")
            
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 1])
            
            with col1:
                overall_score = scores.get('overall_score', 0)
                # Clean the overall_score to ensure it's a number
                try:
                    if isinstance(overall_score, str) and ('<' in overall_score or 'div' in overall_score.lower()):
                        overall_score = 0
                    else:
                        overall_score = int(float(overall_score)) if overall_score else 0
                except (ValueError, TypeError):
                    overall_score = 0
                    
                score_color = ("score-excellent" if overall_score >= 80 else 
                              "score-good" if overall_score >= 60 else
                              "score-warning" if overall_score >= 40 else "score-poor")
                render_flashcard(
                    title=f"{filename[:12]}{'...' if len(filename) > 12 else ''}",
                    value=f"{overall_score}/100",
                    color_class=score_color,
                    progress_value=overall_score
                )
                
            with col2:
                classification = scores.get('classification', 'unknown')
                # Clean classification value aggressively
                if isinstance(classification, str):
                    # Remove any HTML content
                    import re
                    classification = re.sub(r'<[^>]*>', '', str(classification))
                    classification = classification.replace('_', ' ').title()
                    if any(bad in classification.lower() for bad in ['div', 'class', 'style', 'progress']):
                        classification = "Unknown"
                else:
                    classification = "Unknown"
                    
                class_color = ("score-excellent" if classification == 'Accept Ok' else 
                              "score-warning" if classification == 'Accept With Warnings' else "score-poor")
                
                # Create custom metric with smaller font for status to fit better
                st.markdown(f"""
                <div style="background-color: white; border: 1px solid #ddd; border-radius: 8px; padding: 8px; text-align: center;">
                    <div style="font-size: 0.7rem; color: #666; margin-bottom: 4px;">Status</div>
                    <div style="font-size: 0.8rem; font-weight: bold; color: #333; line-height: 1.1;">
                        {classification}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col3:
                statements_score = scores.get('financial_statements_score', 0)
                try:
                    if isinstance(statements_score, str) and ('<' in statements_score or 'div' in statements_score.lower()):
                        statements_score = 0
                    else:
                        statements_score = int(float(statements_score)) if statements_score else 0
                except (ValueError, TypeError):
                    statements_score = 0
                    
                render_flashcard(
                    title="Statements",
                    value=f"{statements_score}/30",
                    progress_value=int((statements_score/30)*100) if statements_score > 0 else 0
                )
                
            with col4:
                performance_score = scores.get('performance_metrics_score', 0)
                try:
                    if isinstance(performance_score, str) and ('<' in performance_score or 'div' in performance_score.lower()):
                        performance_score = 0
                    else:
                        performance_score = int(float(performance_score)) if performance_score else 0
                except (ValueError, TypeError):
                    performance_score = 0
                    
                render_flashcard(
                    title="Performance",
                    value=f"{performance_score}/25",
                    progress_value=int((performance_score/25)*100) if performance_score > 0 else 0
                )
                
            with col5:
                period_score = scores.get('period_evidence_score', 0)
                try:
                    if isinstance(period_score, str) and ('<' in period_score or 'div' in period_score.lower()):
                        period_score = 0
                    else:
                        period_score = int(float(period_score)) if period_score else 0
                except (ValueError, TypeError):
                    period_score = 0
                    
                render_flashcard(
                    title="Period",
                    value=f"{period_score}/25",
                    progress_value=int((period_score/25)*100) if period_score > 0 else 0
                )
                
            with col6:
                numeric_score = scores.get('numeric_content_score', 0)
                try:
                    if isinstance(numeric_score, str) and ('<' in numeric_score or 'div' in numeric_score.lower()):
                        numeric_score = 0
                    else:
                        numeric_score = int(float(numeric_score)) if numeric_score else 0
                except (ValueError, TypeError):
                    numeric_score = 0
                    
                render_flashcard(
                    title="Numeric",
                    value=f"{numeric_score}/20",
                    progress_value=int((numeric_score/20)*100) if numeric_score > 0 else 0
                )
            
            # Show warnings and issues for financial documents
            if classification in ['Accept With Warnings', 'Reject Incomplete']:
                with st.expander(f"⚠️ Financial Issues for {filename}", expanded=False):
                    warnings = []
                    
                    # Financial statement issues
                    if flags.get('no_financial_statements'):
                        warnings.append("**🚨 Missing Financial Statements**: No Profit & Loss, Balance Sheet, or Cash Flow statements found")
                    
                    if flags.get('insufficient_performance_metrics'):
                        warnings.append("**⚠️ Limited Performance Metrics**: Need at least 2 key metrics (Sales, Expenses, Profit, EPS, EBITDA)")
                    
                    if flags.get('missing_period_evidence'):
                        warnings.append("**⚠️ Missing Period Information**: No clear financial year, quarterly, or period references found")
                    
                    if flags.get('minimal_numeric_content'):
                        warnings.append("**⚠️ Insufficient Numeric Data**: Limited financial numbers and amounts detected")
                    
                    if flags.get('likely_cover_page_only'):
                        warnings.append("**⚠️ Cover Page Only**: Document appears to contain only cover/title information")
                    
                    if flags.get('likely_notes_only'):
                        warnings.append("**⚠️ Notes Only**: Document appears to contain only notes without main financial statements")
                    
                    # Add financial analysis anomalies if available
                    financial_data = result.get("financial", {})
                    anomalies = financial_data.get("anomalies", [])
                    if anomalies:
                        warnings.append(f"**🔍 Financial Anomalies**: {'; '.join(anomalies[:3])}")
                    
                    if warnings:
                        for warning in warnings:
                            st.markdown(f"- {warning}")
                    else:
                        st.markdown("- No specific financial issues identified")
                    
                    # Show recommendation
                    if classification == 'Reject Incomplete':
                        st.error("📋 **Recommendation**: Upload complete financial statements with P&L, Balance Sheet, Cash Flow, and clear period information")
                    else:
                        st.info("📋 **Recommendation**: Review financial data completeness and consider uploading additional statements if available")
    
    # Summary stats with flashcards
    st.subheader("Completeness Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    # Legal summary
    if legal_completeness:
        legal_accepted = sum(1 for r in legal_completeness 
                            if r.get("completeness", {}).get("scores", {}).get("classification") in ["accept_ok", "accept_with_warnings"])
        legal_rejected = len(legal_completeness) - legal_accepted
        avg_legal_score = sum(r.get("completeness", {}).get("scores", {}).get("overall_score", 0) 
                             for r in legal_completeness) / len(legal_completeness) if legal_completeness else 0
        
        with col1:
            render_flashcard(
                title="Legal Accepted",
                value=f"{legal_accepted}/{len(legal_completeness)}",
                color_class="score-good" if legal_accepted > 0 else "score-warning",
                progress_value=int((legal_accepted/len(legal_completeness))*100) if legal_completeness else 0
            )
            
        with col2:
            render_flashcard(
                title="Legal Rejected",
                value=str(legal_rejected),
                color_class="score-poor" if legal_rejected > 0 else "score-excellent"
            )
    
    # Financial summary
    if financial_completeness:
        fin_accepted = sum(1 for r in financial_completeness 
                          if r.get("financial_completeness", {}).get("scores", {}).get("classification") in ["accept_ok", "accept_with_warnings"])
        fin_rejected = len(financial_completeness) - fin_accepted
        avg_fin_score = sum(r.get("financial_completeness", {}).get("scores", {}).get("overall_score", 0) 
                           for r in financial_completeness) / len(financial_completeness) if financial_completeness else 0
        
        with col3:
            render_flashcard(
                title="Financial Accepted",
                value=f"{fin_accepted}/{len(financial_completeness)}",
                color_class="score-good" if fin_accepted > 0 else "score-warning",
                progress_value=int((fin_accepted/len(financial_completeness))*100) if financial_completeness else 0
            )
            
        with col4:
            render_flashcard(
                title="Financial Rejected", 
                value=str(fin_rejected),
                color_class="score-poor" if fin_rejected > 0 else "score-excellent"
            )

st.divider()

# Headlines generated from stored outputs (grounded)
st.subheader("Deal Overview Insights")

if st.button("🚀 Generate Deal Insights (3–5)", type="primary"):
    # Build comprehensive deal context from existing results
    bullets = []
    
    # Overall deal risk context
    bullets.append(f"DEAL RISK ASSESSMENT: Overall risk level is {risk} with {high_contracts} high-risk contracts identified")
    bullets.append(f"DOCUMENT COVERAGE: {len(legal_rows)} legal documents and {len(fin_rows)} financial documents analyzed")
    
    # Legal context - focus on deal implications
    for r in legal_rows[:5]:  # Limit to top 5 for context
        legal = r.get("legal", {})
        lvl = legal.get("risk_level")
        reds = legal.get("red_flags", [])
        filename = r.get('filename', 'Unknown')
        if reds:
            bullets.append(f"LEGAL CONCERN - {filename}: {lvl} risk with issues: {', '.join(reds[:2])}")
        elif lvl == "High":
            bullets.append(f"LEGAL REVIEW - {filename}: {lvl} risk level requires attention")

    # Financial context - focus on deal health
    for r in fin_rows[:5]:  # Limit to top 5 for context
        fin = r.get("financial", {})
        an = fin.get("anomalies", [])
        filename = r.get('filename', 'Unknown')
        if an:
            bullets.append(f"FINANCIAL FLAG - {filename}: Anomalies detected: {', '.join(an[:2])}")

    # Add deal-specific completeness insights
    if high_contracts == 0 and med_contracts > 0:
        bullets.append("POSITIVE INDICATOR: No high-risk contracts identified, moderate risk level manageable")
    elif high_contracts > 3:
        bullets.append(f"ATTENTION REQUIRED: {high_contracts} high-risk contracts need detailed review before closing")
    
    context = "\n".join(bullets) if bullets else "No deal analysis data available yet."

    system = (
        "You are a senior M&A advisor and due diligence expert.\n"
        "Generate 3-5 strategic deal insights based ONLY on the provided analysis context.\n"
        "Focus on deal viability, risk assessment, and key decision points for stakeholders.\n"
        "Format as clear bullet points. Do not invent facts beyond what's provided.\n"
        "If data is insufficient, clearly state data limitations.\n"
    )
    user = f"DEAL ANALYSIS CONTEXT:\n{context}\n\nTASK:\nProvide 3-5 strategic deal overview insights for decision makers."

    with st.spinner("🤖 Generating insights..."):
        out = ollama_chat(
            base_url=settings.ollama_base_url,
            model=settings.chat_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        
        # Display insights in a clean, simple format
        if out and out.strip():
            st.success("🎯 Strategic Deal Insights")
            st.markdown(out)
        else:
            st.warning("⚠️ Unable to generate insights with current data. Please ensure documents are analyzed first.")

