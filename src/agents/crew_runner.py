from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from crewai import Agent, Task, Crew, Process  # type: ignore

from src.agents.llm_factory import get_llm_id
from src.agents.schemas import RouterDecision, LegalRiskFinding, FinancialAnomalyFinding
from src.tools.prompts import ROUTER_PROMPT, LEGAL_PROMPT, FIN_PROMPT

@dataclass(frozen=True)
class CrewResults:
    router: RouterDecision
    legal: LegalRiskFinding | None = None
    financial: FinancialAnomalyFinding | None = None

def _safe_parse_json(s: str) -> Dict[str, Any]:
    s = s.strip()
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not find JSON in model output: {s[:250]}")
    return json.loads(s[start:end+1])

def heuristic_doc_type(filename: str, text: str) -> str | None:
    fn = filename.lower()
    t = (text[:8000] or "").lower()

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
    out = crew.kickoff()
    return LegalRiskFinding(**_safe_parse_json(str(out)))

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
    # Heuristic-first routing for MVP reliability
    h = heuristic_doc_type(filename, full_text)
    if h == "contract":
        return CrewResults(router=RouterDecision(doc_type="contract", rationale="Heuristic route"), legal=run_legal(filename, full_text))
    if h == "financial":
        return CrewResults(router=RouterDecision(doc_type="financial", rationale="Heuristic route"), financial=run_financial(filename, full_text))

    # Fallback to LLM router
    router_decision = run_router(filename, full_text[:2500])
    if router_decision.doc_type == "contract":
        return CrewResults(router=router_decision, legal=run_legal(filename, full_text))
    if router_decision.doc_type == "financial":
        return CrewResults(router=router_decision, financial=run_financial(filename, full_text))
    return CrewResults(router=router_decision)
