from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from src.embeddings.ollama_embed import embed_text
from src.extractors.pdf_text import extract_pdf_text
from src.extractors.docx_text import extract_docx_text
from src.extractors.pptx_text import extract_pptx_text
from src.extractors.tabular_text import extract_csv_text, extract_xlsx_text
from src.vectordb.qdrant_store import get_qdrant_local_client

COLLECTION_NAME = "deal_chunks"

@dataclass
class IngestResult:
    filename: str
    chunks_ingested: int

def _point_id(deal_id: str, doc_id: str, chunk_id: int) -> int:
    """Deterministic 64-bit integer point id for Qdrant local mode."""
    key = f"{deal_id}:{doc_id}:{chunk_id}".encode("utf-8")
    h = hashlib.blake2b(key, digest_size=8).digest()
    return int.from_bytes(h, "big", signed=False)

def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks

def _extract_text_for_file(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
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
    raise ValueError(f"Unsupported file type: {ext}")

def _ensure_collection(client: QdrantClient, vector_size: int) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME in existing:
        return
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
    )

def ingest_file_to_qdrant(
    *,
    deal_id: str,
    doc_id: str,
    filename: str,
    stored_path: str,
    ollama_base_url: str,
    embed_model: str,
    qdrant_path: Path,
    client: Optional[QdrantClient] = None,
) -> IngestResult:
    text = _extract_text_for_file(stored_path)
    chunks = _chunk_text(text)

    if not chunks:
        return IngestResult(filename=filename, chunks_ingested=0)

    # Embed first chunk to get vector size
    v0 = embed_text(ollama_base_url, embed_model, chunks[0])
    vector_size = len(v0)

    if client is None:
        client = get_qdrant_local_client(qdrant_path)

    _ensure_collection(client, vector_size)

    # Embed remaining chunks
    vectors = [v0] + [embed_text(ollama_base_url, embed_model, c) for c in chunks[1:]]

    points = []
    for i, (vec, chunk_text) in enumerate(zip(vectors, chunks), start=1):
        payload: Dict[str, Any] = {
            "deal_id": deal_id,
            "doc_id": doc_id,
            "filename": filename,
            "chunk_id": i,
            "text": chunk_text,
        }
        points.append(
            qm.PointStruct(
                id=_point_id(deal_id, doc_id, i),
                vector=vec,
                payload=payload,
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return IngestResult(filename=filename, chunks_ingested=len(points))
