#!/usr/bin/env python3
"""
Fetch top N chunks from Qdrant (basic scroll) and print first 100 chars.

Usage:
  python scripts/rag_fetch_chunks.py                 # fetch 3 chunks
  python scripts/rag_fetch_chunks.py --limit 5       # fetch 5 chunks
  python scripts/rag_fetch_chunks.py --source-id X   # filter by source/document id

Notes:
  - This is Phase 1 helper script: simple retrieval without similarity search.
  - Next steps will filter by selected sources and use vector search.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List

import requests


def scroll_points(
    host: str,
    collection: str,
    limit: int,
    source_id: str | None = None,
) -> List[Dict[str, Any]]:
    url = f"{host}/collections/{collection}/points/scroll"
    payload: Dict[str, Any] = {"limit": limit, "with_payload": True}
    if source_id:
        # Match either document_id (file) or source_id (url) in payload
        payload["filter"] = {
            "should": [
                {"key": "document_id", "match": {"value": source_id}},
                {"key": "source_id", "match": {"value": source_id}},
            ]
        }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to query Qdrant scroll API: {e}")
        sys.exit(1)

    data = resp.json()
    return data.get("result", {}).get("points", [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch chunks from Qdrant (basic scroll)")
    parser.add_argument("--host", default=os.getenv("QDRANT_HTTP", "http://localhost:6333"), help="Qdrant HTTP base URL")
    parser.add_argument("--collection", default=os.getenv("QDRANT_COLLECTION", "documents"), help="Qdrant collection name")
    parser.add_argument("--limit", type=int, default=3, help="Number of chunks to fetch (default: 3)")
    parser.add_argument("--source-id", help="Filter by source/document id in payload")
    parser.add_argument(
        "--selected-sources",
        help="Comma-separated list of source/document ids to filter (respects either document_id or source_id)",
    )

    args = parser.parse_args()

    # Build combined filter if multiple sources provided
    points: List[Dict[str, Any]] = []
    if args.selected_sources:
        ids = [s.strip() for s in args.selected_sources.split(",") if s.strip()]
        remaining = args.limit
        for sid in ids:
            if remaining <= 0:
                break
            batch = scroll_points(args.host, args.collection, remaining, sid)
            points.extend(batch)
            remaining = args.limit - len(points)
    else:
        points = scroll_points(args.host, args.collection, args.limit, args.source_id)
    if not points:
        print("📭 No chunks found in Qdrant.")
        return

    print(f"📄 Showing {len(points)} chunk(s) from '{args.collection}' (host: {args.host})")
    for idx, pt in enumerate(points, 1):
        payload = pt.get("payload", {})
        # Prefer 'chunk_text' (our current payload field), fallback to 'text' or 'chunk'
        text = payload.get("chunk_text") or payload.get("text") or payload.get("chunk") or ""
        prefix = (text[:100] + "…") if len(text) > 100 else text
        owner = payload.get("owner_id")
        src_type = payload.get("source_type")
        url = payload.get("url")
        doc_id = payload.get("document_id") or payload.get("source_id")
        print(f"{idx}. id={pt.get('id')} owner={owner} type={src_type} ref={doc_id}")
        if url:
            print(f"   url={url}")
        if text:
            print(f"   text: {prefix}")
        else:
            # Show raw payload for debugging when text is missing
            import json
            print("   text: <empty>")
            print("   payload:")
            try:
                print("   " + json.dumps(payload, indent=2).replace("\n", "\n   "))
            except Exception:
                print(f"   {payload}")


if __name__ == "__main__":
    main()


