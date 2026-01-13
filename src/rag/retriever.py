from __future__ import annotations

from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

COLLECTION_NAME = "deal_chunks"

def _query(client: QdrantClient, query_vector: List[float], top_k: int, flt: qm.Filter | None):
    return client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        query_filter=flt,
        with_payload=True,
    ).points

def _hits_from_points(points) -> List[Dict[str, Any]]:
    hits = []
    for p in points:
        payload = p.payload or {}
        hits.append(
            {
                "score": float(p.score) if p.score is not None else None,
                "text": payload.get("text", ""),
                "filename": payload.get("filename", "unknown"),
                "chunk_id": payload.get("chunk_id", payload.get("chunk_index", "na")),
                "payload": payload,
            }
        )
    return hits

def retrieve_chunks(
    client: QdrantClient,
    deal_id: str,
    query_vector: List[float],
    top_k: int = 6,
) -> List[Dict[str, Any]]:
    # 1) Try strict filter on deal_id
    flt1 = qm.Filter(must=[qm.FieldCondition(key="deal_id", match=qm.MatchValue(value=deal_id))])
    pts = _query(client, query_vector, top_k, flt1)

    # 2) If empty, try alternate key dealId
    if not pts:
        flt2 = qm.Filter(must=[qm.FieldCondition(key="dealId", match=qm.MatchValue(value=deal_id))])
        pts = _query(client, query_vector, top_k, flt2)

    # 3) If still empty, query without filter and client-side filter
    if not pts:
        pts_any = _query(client, query_vector, top_k=50, flt=None)
        hits_any = _hits_from_points(pts_any)
        filtered = []
        for h in hits_any:
            pl = h.get("payload", {})
            if pl.get("deal_id") == deal_id or pl.get("dealId") == deal_id or pl.get("deal") == deal_id:
                filtered.append(h)
        return filtered[:top_k]

    hits = _hits_from_points(pts)
    return hits[:top_k]
