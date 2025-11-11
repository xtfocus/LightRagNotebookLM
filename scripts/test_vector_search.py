#!/usr/bin/env python3
"""
Phase 1: Basic vector search with cached query embeddings.

- Generates an embedding for a text query (uses OpenAI if not cached)
- Searches Qdrant for top-N similar chunks
- Prints first 100 characters of each chunk

Usage:
  python scripts/test_vector_search.py --query "What is machine learning?"
  python scripts/test_vector_search.py --query "..." --limit 5 --score 0.6
  python scripts/test_vector_search.py --query "..." --owner-id <uuid>

Env:
  OPENAI_API_KEY must be set if embedding is not cached yet (you can `source .env`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


# Try to import the shared qdrant manager from indexing_worker, falling back to REST
def _import_qdrant_manager():
    """Optionally import in-project manager (used inside containers).

    When running on host, prefer REST using QDRANT_HTTP (like rag_fetch_chunks.py).
    """
    # Prefer REST path to match scripts/rag_fetch_chunks.py behavior
    return ("rest", None)


def _create_embedding(query: str, model: str, api_key: str) -> List[float]:
    """Create an embedding using either OpenAI v1 client or legacy API."""
    # Try v1 style client first
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key)
        resp = client.embeddings.create(model=model, input=[query])
        return resp.data[0].embedding
    except Exception:
        pass
    # Fallback to legacy interface
    try:
        import openai  # type: ignore
        openai.api_key = api_key
        # Prefer modern lowercase API if available
        if hasattr(openai, "embeddings") and hasattr(openai.embeddings, "create"):
            resp = openai.embeddings.create(model=model, input=[query])
            return resp.data[0].embedding
        # Legacy capitalized API
        if hasattr(openai, "Embeddings"):
            resp = openai.Embeddings.create(model=model, input=[query])
            return resp.data[0].embedding
        raise RuntimeError("openai python package lacks embeddings API")
    except Exception as e:
        raise RuntimeError(f"Failed to create embedding with OpenAI client(s): {e}")


def load_cache(cache_file: Path) -> Dict[str, Any]:
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache_file: Path, data: Dict[str, Any]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2))


def get_query_embedding(query: str, model: str, cache_file: Path) -> List[float]:
    cache = load_cache(cache_file)
    if query in cache:
        return cache[query]

    # Not cached, call OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set and embedding is not cached.")

    embedding = _create_embedding(query, model, api_key)

    cache[query] = embedding
    save_cache(cache_file, cache)
    return embedding


def search_with_manager(qdrant_mgr, query_embedding: List[float], limit: int, score: float, owner_id: str | None):
    return qdrant_mgr.search_similar(
        query_embedding=query_embedding,
        limit=limit,
        score_threshold=score,
        owner_id=owner_id,
    )


def search_with_rest(query_embedding: List[float], limit: int, score: float, owner_id: str | None = None) -> List[Dict[str, Any]]:
    # Minimal REST fallback if import fails (no owner filter here for simplicity)
    import requests
    host = os.getenv("QDRANT_HTTP", "http://localhost:6333")
    collection = os.getenv("QDRANT_COLLECTION", "documents")
    url = f"{host}/collections/{collection}/points/search"
    payload: Dict[str, Any] = {
        "vector": query_embedding,
        "limit": limit,
        "score_threshold": score,
        "with_payload": True,
    }
    if owner_id:
        payload["filter"] = {
            "must": [
                {"key": "owner_id", "match": {"value": owner_id}}
            ]
        }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    results = r.json().get("result", [])
    out: List[Dict[str, Any]] = []
    for res in results:
        out.append({"id": res.get("id"), "score": res.get("score"), "payload": res.get("payload", {})})
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Basic vector search with cached embeddings")
    parser.add_argument("--query", required=True, help="Natural language query text")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "text-embedding-3-small"))
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--score", type=float, default=0.7)
    parser.add_argument("--owner-id", help="Optional owner_id filter (if using manager)")
    parser.add_argument("--cache-file", default=str(Path("scripts/.embeddings_cache.json")))

    args = parser.parse_args()

    cache_file = Path(args.cache_file)
    embedding = get_query_embedding(args.query, args.model, cache_file)

    mode, mgr = _import_qdrant_manager()
    if mode == "manager" and mgr is not None:
        results = search_with_manager(mgr, embedding, args.limit, args.score, args.owner_id)
    else:
        # REST path aligns with scripts/rag_fetch_chunks.py (host localhost by default)
        results = search_with_rest(embedding, args.limit, args.score, args.owner_id)

    if not results:
        print("📭 No results.")
        return

    print(f"🔎 Query: {args.query}")
    print(f"📈 Top {len(results)} results (score ≥ {args.score}):")
    for i, res in enumerate(results, 1):
        payload = res.get("payload", {})
        text = payload.get("chunk_text") or payload.get("text") or payload.get("chunk") or ""
        prefix = (text[:100] + "…") if len(text) > 100 else text
        print(f"{i}. score={res.get('score'):.3f} id={res.get('id')} owner={payload.get('owner_id')} ref={payload.get('document_id')}")
        if payload.get("url"):
            print(f"   url={payload.get('url')}")
        print(f"   text: {prefix}")


if __name__ == "__main__":
    main()


