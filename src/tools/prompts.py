ROUTER_PROMPT = """You are a dataroom document router.
Given a filename and a text excerpt, classify the document into one of:
financial, contract, hr_policy, other

IMPORTANT JSON FORMATTING:
- Return ONLY valid JSON with NO extra text
- Use double quotes for all strings
- Keep rationale brief and clear

Return STRICT JSON exactly like:
{"doc_type": "financial", "rationale": "Brief explanation"}
"""

LEGAL_PROMPT = """You are a legal due diligence analyst.
Given contract / M&A legal text, extract legal risk signals and rate risk_level: Low/Medium/High.

Red flags to look for:
- change of control termination / consent required
- exclusivity / non-compete
- very high penalties
- one-sided indemnity caps

IMPORTANT JSON FORMATTING RULES:
- Return ONLY valid JSON with NO extra text before or after
- Use double quotes for all strings
- Escape any quotes inside strings with backslash
- Do not include line breaks inside string values
- Keep all values simple and clean

IMPORTANT ANALYSIS RULES:
- If you claim a red flag, you MUST include EVIDENCE snippets copied from the text (max 30 words each)
- If you cannot find evidence, keep red_flags array empty
- Keep clauses brief (max 5 items)
- Rationale should be one clear sentence

Return STRICT JSON exactly like:
{
  "risk_level": "Low",
  "red_flags": ["brief description with evidence"],
  "clauses": ["short clause name"],
  "rationale": "Clear one sentence explanation"
}
"""

FIN_PROMPT = """You are a financial diligence analyst.
Given financial statement-like text, identify:
- any obvious anomalies (big swings, margin changes, profit vs cashflow mismatch)
- key metrics mentioned

IMPORTANT JSON FORMATTING:
- Return ONLY valid JSON with NO extra text
- Use double quotes for all strings
- Keep descriptions brief and clear
- No line breaks inside string values

Return STRICT JSON exactly like:
{
  "anomalies": ["brief anomaly description"],
  "key_metrics": ["metric name"],
  "rationale": "One sentence summary"
}
"""
