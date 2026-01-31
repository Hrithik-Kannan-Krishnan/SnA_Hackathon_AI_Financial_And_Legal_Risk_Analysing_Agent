from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from crewai import Agent, Task, Crew, Process  # type: ignore

from src.agents.llm_factory import get_llm_id
from src.agents.schemas import RouterDecision, LegalRiskFinding, FinancialAnomalyFinding
from src.agents.deal_completeness_analyzer import DealCompletenessAnalyzer
from src.agents.deal_completeness_schema import DealCompletenessAnalysis
from src.agents.financial_completeness_analyzer import FinancialCompletenessAnalyzer
from src.agents.financial_completeness_schema import FinancialCompletenessAnalysis
from src.tools.prompts import ROUTER_PROMPT, LEGAL_PROMPT, FIN_PROMPT

@dataclass(frozen=True)
class CrewResults:
    router: RouterDecision
    legal: LegalRiskFinding | None = None
    financial: FinancialAnomalyFinding | None = None
    completeness: DealCompletenessAnalysis | None = None
    financial_completeness: FinancialCompletenessAnalysis | None = None

def _safe_parse_json(s: str) -> Dict[str, Any]:
    import re
    
    # Clean the string first
    s = s.strip()
    
    # Remove or escape invalid control characters
    # Keep only valid control characters (tab, newline, carriage return)
    s = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', s)
    
    # Fix common JSON formatting issues
    s = re.sub(r'[\r\n]+', ' ', s)  # Replace newlines with spaces
    s = re.sub(r'\s+', ' ', s)  # Collapse multiple spaces
    
    # Find JSON boundaries
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not find JSON in model output: {s[:250]}")
    
    json_str = s[start:end+1]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        try:
            # Fix unescaped quotes in strings
            fixed_json = re.sub(r'(?<!\\)"(?![,\]}:])', r'\"', json_str)
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            # Last resort: try to extract key-value pairs manually
            try:
                # Simple fallback for basic JSON objects
                fallback_data = {}
                
                # Extract risk_level
                risk_match = re.search(r'"risk_level"\s*:\s*"([^"]*)"', json_str)
                if risk_match:
                    fallback_data["risk_level"] = risk_match.group(1)
                else:
                    fallback_data["risk_level"] = "Medium"  # default
                
                # Extract red_flags
                flags_match = re.search(r'"red_flags"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                if flags_match:
                    flags_str = flags_match.group(1)
                    # Simple extraction of quoted strings
                    flags = re.findall(r'"([^"]*)"', flags_str)
                    fallback_data["red_flags"] = flags[:5]  # limit to 5
                else:
                    fallback_data["red_flags"] = []
                
                # Extract clauses
                clauses_match = re.search(r'"clauses"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                if clauses_match:
                    clauses_str = clauses_match.group(1)
                    clauses = re.findall(r'"([^"]*)"', clauses_str)
                    fallback_data["clauses"] = clauses[:5]  # limit to 5
                else:
                    fallback_data["clauses"] = []
                
                # Extract rationale
                rationale_match = re.search(r'"rationale"\s*:\s*"([^"]*)"', json_str)
                if rationale_match:
                    fallback_data["rationale"] = rationale_match.group(1)
                else:
                    fallback_data["rationale"] = "Analysis completed with parsing issues"
                
                return fallback_data
                
            except Exception:
                # Ultimate fallback
                return {
                    "risk_level": "Medium",
                    "red_flags": ["JSON parsing error occurred"],
                    "clauses": [],
                    "rationale": f"Failed to parse LLM response due to JSON formatting issues. Raw output: {json_str[:200]}..."
                }

def heuristic_doc_type(filename: str, text: str) -> str | None:
    fn = filename.lower()
    t = (text[:8000] or "").lower()
    
    # Step 1: Detect file extension first for financial spreadsheets
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    if ext in ['.xlsx', '.xls', '.csv']:
        return "financial"  # Always treat spreadsheets as financial

    # Treat M&A/legal analysis PDFs as legal pipeline for MVP
    legal_kw = [
        "merger", "m&a", "acquisition", "scheme of arrangement", "terms of merger",
        "nclt", "cci", "sebi", "regulatory", "consent", "termination", "change of control",
        "exclusivity", "non-compete", "indemnity", "penalty", "governing law",
        "confidentiality", "cross-border merger",
    ]
    if any(k in fn for k in ["m&a", "merger", "reliance", "disney", "uniliver", "unilever", "pvr", "inox", "vodafone"]) or any(k in t for k in legal_kw):
        return "contract"

    fin_kw = ["income statement", "balance sheet", "cash flow", "ebitda", "net income", "revenue", "cogs"]
    if any(k in fn for k in ["income", "balance", "cashflow", "financial"]) or any(k in t for k in fin_kw):
        return "financial"

    return None

def run_router(filename: str, excerpt: str) -> RouterDecision:
    llm_id = get_llm_id()
    router = Agent(
        role="Router Agent",
        goal="Classify dataroom documents into correct doc_type for downstream pipelines.",
        backstory="You route documents for a due diligence copilot system.",
        llm=llm_id,
        allow_delegation=False,
        verbose=False,
    )
    task = Task(
        description=f"{ROUTER_PROMPT}\n\nFILENAME:\n{filename}\n\nEXCERPT:\n{excerpt}",
        expected_output='STRICT JSON like {"doc_type":"contract","rationale":"..."}',
        agent=router,
    )
    crew = Crew(agents=[router], tasks=[task], process=Process.sequential, verbose=False, tracing=False)
    out = crew.kickoff()
    data = _safe_parse_json(str(out))
    return RouterDecision(**data)

def run_legal(filename: str, text: str) -> LegalRiskFinding:
    llm_id = get_llm_id()
    a = Agent(
        role="Legal Risk Agent",
        goal="Extract key legal risks and rate risk level.",
        backstory="Careful due diligence analyst. Use only provided text.",
        llm=llm_id,
        allow_delegation=False,
        verbose=False,
    )
    task = Task(
        description=f"{LEGAL_PROMPT}\n\nFILENAME:\n{filename}\n\nTEXT:\n{text[:12000]}",
        expected_output="STRICT JSON with risk_level, red_flags, clauses, rationale.",
        agent=a,
    )
    crew = Crew(agents=[a], tasks=[task], process=Process.sequential, verbose=False, tracing=False)
    
    try:
        out = crew.kickoff()
        parsed_data = _safe_parse_json(str(out))
        return LegalRiskFinding(**parsed_data)
    except Exception as e:
        print(f"Warning: Legal analysis failed for {filename}: {e}")
        # Return a safe fallback result
        return LegalRiskFinding(
            risk_level="Medium",
            red_flags=[f"Analysis error: {str(e)[:100]}"],
            clauses=[],
            rationale=f"Could not complete analysis due to parsing error: {str(e)[:100]}"
        )

def run_financial(filename: str, text: str) -> FinancialAnomalyFinding:
    llm_id = get_llm_id()
    a = Agent(
        role="Financial Analysis Agent",
        goal="Extract key metrics and flag anomalies (MVP).",
        backstory="Financial diligence analyst for statements/schedules.",
        llm=llm_id,
        allow_delegation=False,
        verbose=False,
    )
    task = Task(
        description=f"{FIN_PROMPT}\n\nFILENAME:\n{filename}\n\nTEXT:\n{text[:12000]}",
        expected_output="STRICT JSON with anomalies, key_metrics, rationale.",
        agent=a,
    )
    crew = Crew(agents=[a], tasks=[task], process=Process.sequential, verbose=False, tracing=False)
    out = crew.kickoff()
    return FinancialAnomalyFinding(**_safe_parse_json(str(out)))

def run_pipeline(filename: str, full_text: str) -> CrewResults:
    """
    Enhanced pipeline with document-type-aware completeness validation.
    Uses different validation rules for legal vs financial documents.
    """
    # First, determine document type for completeness analysis
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    
    # Step 2: Use document-type-aware completeness analysis
    if ext in ['.xlsx', '.xls', '.csv']:
        # Financial spreadsheet - use financial completeness rules
        financial_analyzer = FinancialCompletenessAnalyzer()
        financial_completeness = financial_analyzer.analyze_document(filename, full_text)
        
        # Check financial document completeness
        if financial_completeness.scores.classification == "reject_incomplete":
            return CrewResults(
                router=RouterDecision(
                    doc_type="financial", 
                    rationale=f"Financial document rejected: Missing core financial statements or insufficient data. "
                             f"Score: {financial_completeness.scores.overall_score}/100. "
                             f"Financial statements: {financial_completeness.scores.financial_statements_score}/30, "
                             f"Performance metrics: {financial_completeness.scores.performance_metrics_score}/25."
                ),
                financial_completeness=financial_completeness
            )
        
        # Process as financial document
        return CrewResults(
            router=RouterDecision(doc_type="financial", rationale="Financial spreadsheet - heuristic route"), 
            financial=run_financial(filename, full_text),
            financial_completeness=financial_completeness
        )
    
    else:
        # Legal/contract document - use legal completeness rules
        analyzer = DealCompletenessAnalyzer()
        completeness_analysis = analyzer.analyze_document(filename, full_text)
        
        # Check legal document completeness (but allow financial documents through)
        h = heuristic_doc_type(filename, full_text)
        
        # Skip legal completeness check for financial documents
        if h != "financial" and completeness_analysis.scores.classification == "reject_incomplete":
            return CrewResults(
                router=RouterDecision(
                    doc_type="other", 
                    rationale=f"Document rejected: {completeness_analysis.flags.missing_core_buckets}. "
                             f"Insufficient deal detail - likely teaser/summary/incomplete extract. "
                             f"Coverage: {completeness_analysis.scores.bucket_coverage_score}/70 points."
                ),
                completeness=completeness_analysis
            )
        
        # Continue with existing logic for legal/contract documents
        if h == "contract":
            legal_result = run_legal(filename, full_text)
            
            # Apply completeness constraints to legal analysis (only for legal docs)
            if completeness_analysis.scores.classification == "reject_incomplete":
                legal_result.risk_level = "High"
                legal_result.red_flags.append("INCOMPLETE DOCUMENT: Insufficient bucket coverage for reliable analysis")
            
            return CrewResults(
                router=RouterDecision(doc_type="contract", rationale="Heuristic route"), 
                legal=legal_result,
                completeness=completeness_analysis
            )
        
        if h == "financial":
            # For financial PDFs, use financial completeness analysis
            financial_analyzer = FinancialCompletenessAnalyzer()
            financial_completeness = financial_analyzer.analyze_document(filename, full_text)
            
            return CrewResults(
                router=RouterDecision(doc_type="financial", rationale="Heuristic route"), 
                financial=run_financial(filename, full_text),
                financial_completeness=financial_completeness
            )

        # Fallback to LLM router
        router_decision = run_router(filename, full_text[:2500])
        if router_decision.doc_type == "contract":
            legal_result = run_legal(filename, full_text)
            
            # Apply completeness constraints
            if completeness_analysis.scores.classification == "reject_incomplete":
                legal_result.risk_level = "High"
                legal_result.red_flags.append("INCOMPLETE DOCUMENT: Insufficient bucket coverage for reliable analysis")
            
            return CrewResults(
                router=router_decision, 
                legal=legal_result,
                completeness=completeness_analysis
            )
        
        if router_decision.doc_type == "financial":
            # For financial documents routed by LLM, use financial completeness
            financial_analyzer = FinancialCompletenessAnalyzer()
            financial_completeness = financial_analyzer.analyze_document(filename, full_text)
            
            return CrewResults(
                router=router_decision, 
                financial=run_financial(filename, full_text),
                financial_completeness=financial_completeness
            )
        
        return CrewResults(router=router_decision, completeness=completeness_analysis)
