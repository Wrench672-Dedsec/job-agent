from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

from app.config import settings
from app.graph.state import InvestmentJobState

logger = logging.getLogger(__name__)

# ── case loader ───────────────────────────────────────────────────────────────────

def _load_cases(path: Path) -> List[dict]:
    if not path.exists():
        logger.warning("RAG cases file not found: %s", path)
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse RAG cases JSON: %s", exc)
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def _case_to_doc(case: dict) -> str:
    """Flatten a case dict into a single string for embedding."""
    parts = [
        case.get("background") or case.get("candidate_background") or "",
        case.get("problem") or case.get("issue") or "",
        case.get("result") or case.get("outcome") or "",
        case.get("key_lesson") or case.get("recommendation") or "",
        case.get("job_type") or "",
        case.get("sector") or "",
        case.get("city") or "",
    ]
    return " ".join(p for p in parts if p).strip()


# ── chromadb retrieval (optional dependency) ───────────────────────────────────────

def _retrieve_chromadb(
    query: str, cases: List[dict], top_k: int = 5
) -> List[dict]:
    """
    Embed `cases` into an in-memory Chroma collection and return the
    `top_k` most similar to `query`.
    Falls back silently if chromadb is not installed.
    """
    try:
        import chromadb  # type: ignore
        from chromadb.utils.embedding_functions import (
            DefaultEmbeddingFunction,  # type: ignore
        )
    except ImportError:
        logger.debug("chromadb not installed; skipping vector retrieval.")
        return []

    ef = DefaultEmbeddingFunction()  # uses all-MiniLM-L6-v2 via onnx, no API key
    client = chromadb.Client()  # in-memory
    col_name = "job_cases"
    # delete previous collection to avoid stale data across hot-reloads
    try:
        client.delete_collection(col_name)
    except Exception:
        pass
    col = client.create_collection(col_name, embedding_function=ef)

    docs = [_case_to_doc(c) for c in cases]
    ids = [str(i) for i in range(len(cases))]
    # chroma requires non-empty docs
    valid = [(i, d, c) for i, d, c in zip(ids, docs, cases) if d.strip()]
    if not valid:
        return []

    v_ids, v_docs, v_cases = zip(*valid)
    col.add(documents=list(v_docs), ids=list(v_ids))

    results = col.query(query_texts=[query], n_results=min(top_k, len(v_cases)))
    hit_ids = results["ids"][0] if results["ids"] else []
    index_map = {vid: vc for vid, vc in zip(v_ids, v_cases)}
    return [index_map[hid] for hid in hit_ids if hid in index_map]


# ── public agent ────────────────────────────────────────────────────────────────────

def rag_agent(state: InvestmentJobState) -> Dict[str, List[dict]]:
    cases = _load_cases(settings.rag_cases_path)
    if not cases:
        return {"rag_cases": []}

    # Build a retrieval query from available state
    jd_profile = state.get("jd_profile", {})
    resume_snippet = (state.get("resume_text") or "")[:400]
    query_parts = [
        jd_profile.get("job_type") or "",
        jd_profile.get("sector") or "",
        jd_profile.get("city") or "",
        resume_snippet,
    ]
    query = " ".join(p for p in query_parts if p).strip() or "equity research job search"

    retrieved = _retrieve_chromadb(query, cases, top_k=5)
    if not retrieved:
        # chromadb not installed — fall back to first-5 slice
        logger.info("RAG: falling back to top-5 slice (chromadb unavailable).")
        retrieved = cases[:5]

    return {"rag_cases": retrieved}
