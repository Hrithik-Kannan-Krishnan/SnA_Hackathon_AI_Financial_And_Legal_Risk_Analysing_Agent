from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".csv", ".zip"}

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str = ""

def validate_filename(filename: str, allowed_exts: Iterable[str] = ALLOWED_EXTENSIONS) -> ValidationResult:
    if not filename or "." not in filename:
        return ValidationResult(False, "File has no extension.")
    ext = "." + filename.split(".")[-1].lower()
    if ext not in set(allowed_exts):
        return ValidationResult(False, f"Unsupported file type: {ext}. Allowed: {sorted(allowed_exts)}")
    return ValidationResult(True, "")

def validate_size(num_bytes: int, max_bytes: int) -> ValidationResult:
    if num_bytes <= 0:
        return ValidationResult(False, "File is empty.")
    if num_bytes > max_bytes:
        mb = max_bytes / (1024 * 1024)
        return ValidationResult(False, f"File too large. Max allowed: {mb:.0f} MB.")
    return ValidationResult(True, "")
