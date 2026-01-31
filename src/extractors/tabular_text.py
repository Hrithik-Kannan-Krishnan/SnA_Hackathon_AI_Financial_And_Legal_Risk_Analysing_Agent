from __future__ import annotations
import pandas as pd

def extract_csv_text(path: str, max_rows: int = 200) -> str:
    df = pd.read_csv(path)
    return df.head(max_rows).to_csv(index=False)

def extract_xlsx_text(path: str, max_rows: int = 200) -> str:
    xls = pd.ExcelFile(path)
    parts = []
    for sheet in xls.sheet_names[:5]:
        df = xls.parse(sheet).head(max_rows)
        parts.append(f"Sheet: {sheet}\n{df.to_csv(index=False)}")
    return "\n\n".join(parts)
