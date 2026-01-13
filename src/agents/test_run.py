from __future__ import annotations

import json
from pathlib import Path

from src.extractors.pdf_text import extract_pdf_text
from src.agents.crew_runner import run_pipeline

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--pdf", required=True, help="Path to a PDF file")
    args = p.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    text = extract_pdf_text(str(pdf_path))
    if not text.strip():
        raise SystemExit("No text extracted from PDF (OCR comes later).")

    res = run_pipeline(pdf_path.name, text)

    out = {
        "router": res.router.model_dump(),
        "legal": res.legal.model_dump() if res.legal else None,
        "financial": res.financial.model_dump() if res.financial else None,
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
