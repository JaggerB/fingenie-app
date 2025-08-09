from __future__ import annotations

import os
import json
from typing import List, Dict, Optional, Tuple

try:
    import chromadb  # type: ignore
    from chromadb.utils import embedding_functions  # type: ignore
    CHROMA_AVAILABLE = True
except Exception:
    CHROMA_AVAILABLE = False


class LocalVectorStore:
    """Minimal wrapper for a local Chroma collection with optional OpenAI embeddings.

    Falls back to a no-op in-memory index if Chroma is not available.
    """

    def __init__(self, path: str = ".vectordb", collection: str = "excel_docs") -> None:
        self.path = path
        self.collection_name = collection
        self._client = None
        self._col = None
        # Always have an in-memory fallback buffer
        self._mem: List[Dict] = []

        self._use_openai = bool(os.environ.get("OPENAI_EMBEDDINGS"))
        self._openai_model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        if CHROMA_AVAILABLE:
            os.makedirs(self.path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.path)
            self._col = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=(
                    embedding_functions.OpenAIEmbeddingFunction(
                        api_key=os.environ.get("OPENAI_API_KEY"), model_name=self._openai_model
                    ) if self._use_openai else None
                ),
            )
        else:
            # Chroma not available; use in-memory index only
            pass

    def _embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        if CHROMA_AVAILABLE:
            return None  # handled by collection's embedding_function when None, or inside add if provided
        # naive fallback: no vectors, use substring scoring at query time
        return None

    def add(self, ids: List[str], texts: List[str], metadatas: List[Dict]) -> None:
        # Only use Chroma when an embedding function is configured; otherwise use in-memory fallback
        if CHROMA_AVAILABLE and self._col is not None and getattr(self, "_use_openai", False):
            self._col.add(ids=ids, documents=texts, metadatas=metadatas)
            return
        for i, t, m in zip(ids, texts, metadatas):
            self._mem.append({"id": i, "text": t, "metadata": m})

    def query(self, text: str, where: Optional[Dict] = None, k: int = 8) -> List[Tuple[str, str, Dict]]:
        if CHROMA_AVAILABLE and self._col is not None and getattr(self, "_use_openai", False):
            res = self._col.query(query_texts=[text], n_results=k, where=where or {})
            docs = res.get("documents", [[]])[0]
            ids = res.get("ids", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            return list(zip(ids, docs, metas))

        # fallback simple scoring over tuples (id, text, metadata)
        items: List[Tuple[str, str, Dict]] = [
            (m.get("id", ""), m.get("text", ""), m.get("metadata", {})) for m in self._mem
        ]
        if where:
            def ok(md: Dict) -> bool:
                return all(str(md.get(k)) == str(v) for k, v in where.items())
            items = [it for it in items if ok(it[2])]
        items.sort(key=lambda it: it[1].lower().count(text.lower()), reverse=True)
        return items[:k]


