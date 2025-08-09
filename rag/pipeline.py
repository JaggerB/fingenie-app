from __future__ import annotations

from typing import Dict, List
import pandas as pd

from retrieval.vector_store import LocalVectorStore


def build_evidence_pack(query: str, facts_df: pd.DataFrame, store: LocalVectorStore, filters: Dict | None = None) -> Dict:
    results = store.query(query, where=filters or {}, k=6)
    citations: List[Dict] = []
    for _id, text, meta in results:
        # Basic citation from metadata
        citations.append({
            "id": _id,
            "sheet": meta.get("sheet"),
            "doc": meta.get("doc"),
            "row": meta.get("row"),
            "excerpt": text[:200]
        })

    # Attempt deterministic aggregates from facts
    aggregates = {}
    if not facts_df.empty and "Amount" in facts_df.columns:
        try:
            total = float(facts_df["Amount"].sum())
            count = int(facts_df.shape[0])
            aggregates = {"total": total, "count": count}
        except Exception:
            aggregates = {}

    return {"citations": citations, "aggregates": aggregates}


