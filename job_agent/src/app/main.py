from __future__ import annotations

import json
import os
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import settings
from app.graph.graph import compiled_graph          # pre-compiled singleton
from app.schemas.models import RunRequest, RunResponse
from app.web import render_index_page

app = FastAPI(title="Job Agent", version="0.1.0")


# ── startup ───────────────────────────────────────────────────────────────────

def _ensure_dirs() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.seed_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
def _startup() -> None:
    _ensure_dirs()


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_initial_state(payload: RunRequest) -> dict:
    """Convert the API request into a LangGraph initial state dict.

    Merges the convenience ``jd_url`` field into ``jd_urls`` so downstream
    agents never need to handle two separate fields.
    """
    state = payload.model_dump(
        exclude={"llm_provider", "llm_model", "jd_url"}  # strip non-state fields
    )

    # Merge single jd_url into jd_urls list (dedup)
    if payload.jd_url:
        seen = set(state.get("jd_urls") or [])
        if payload.jd_url not in seen:
            state["jd_urls"] = list(seen | {payload.jd_url})

    return state


def _build_response(result: dict) -> RunResponse:
    return RunResponse(
        # Core
        jd_profile      = result.get("jd_profile", {}),
        diagnosis       = result.get("diagnosis", {}),
        resume_versions = result.get("resume_versions", {}),
        final_report    = result.get("final_report", ""),

        # Interview pipeline
        question_bank       = result.get("question_bank", {}),
        interview_map       = result.get("interview_map", {}),
        interview_questions = result.get("interview_questions", []),

        # Coaching pipeline
        coaching_session = result.get("coaching_session", {}),
        coaching_flow    = result.get("coaching_flow", {}),

        # Supporting
        cover_letters     = result.get("cover_letters", []),
        networking_drafts = result.get("networking_drafts", {}),
        rag_cases         = result.get("rag_cases", []),
        collected_jds     = result.get("collected_jds", []),
    )


# ── routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(render_index_page())


@app.post("/run", response_model=RunResponse)
async def run_agent(payload: RunRequest) -> RunResponse:
    """Run the full job-agent pipeline and return the complete result.

    Typical wall-clock time: 30-120 s depending on LLM latency.
    For real-time node progress, use ``POST /run/stream`` instead.
    """
    if payload.llm_provider:
        os.environ["LLM_PROVIDER"] = payload.llm_provider
    if payload.llm_model:
        os.environ["LLM_MODEL"] = payload.llm_model

    state = _build_initial_state(payload)
    result = await compiled_graph.ainvoke(state)   # non-blocking async invoke
    return _build_response(result)


@app.post("/run/stream")
async def run_agent_stream(payload: RunRequest) -> StreamingResponse:
    """Stream node-level progress as newline-delimited JSON (NDJSON).

    Each line is a JSON object::

        {"node": "jd_scraper",    "status": "start"}
        {"node": "jd_scraper",    "status": "done",  "output": {...}}
        {"node": "jd_parser",     "status": "start"}
        ...
        {"node": "__end__",       "status": "done",  "output": <RunResponse JSON>}

    Clients can display a live progress bar by tracking ``status=start/done``
    events per node.
    """
    if payload.llm_provider:
        os.environ["LLM_PROVIDER"] = payload.llm_provider
    if payload.llm_model:
        os.environ["LLM_MODEL"] = payload.llm_model

    state = _build_initial_state(payload)

    async def _event_generator() -> AsyncGenerator[str, None]:
        final_state: dict = {}

        async for event in compiled_graph.astream(state, stream_mode="updates"):
            # ``event`` is a dict: {node_name: {state_updates}}
            for node_name, node_output in event.items():
                if node_name == "__end__":
                    continue

                # Emit a lightweight "done" event per node.
                # Keep node output small: only send keys that changed.
                yield json.dumps(
                    {"node": node_name, "status": "done", "keys": list(node_output.keys())}
                ) + "\n"

                final_state.update(node_output)

        # Final event: full RunResponse
        response = _build_response(final_state)
        yield json.dumps(
            {"node": "__end__", "status": "done", "output": response.model_dump()}
        ) + "\n"

    return StreamingResponse(
        _event_generator(),
        media_type="application/x-ndjson",
    )
