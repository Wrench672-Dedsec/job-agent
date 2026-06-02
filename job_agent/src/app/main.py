from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

from app.config import settings
from app.graph.graph import build_graph
from app.schemas.models import RunRequest, RunResponse
from app.web import render_index_page

app = FastAPI(title="Job Agent", version="0.1.0")
_graph = build_graph()


def _ensure_dirs() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.seed_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
def _startup() -> None:
    _ensure_dirs()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return HTMLResponse(render_index_page())


@app.post("/run", response_model=RunResponse)
def run_agent(payload: RunRequest) -> RunResponse:
    if payload.llm_provider:
        os.environ["LLM_PROVIDER"] = payload.llm_provider
    if payload.llm_model:
        os.environ["LLM_MODEL"] = payload.llm_model

    state = payload.model_dump()
    result = _graph.invoke(state)
    return RunResponse(
        jd_profile=result.get("jd_profile", {}),
        diagnosis=result.get("diagnosis", {}),
        resume_versions=result.get("resume_versions", {}),
        interview_questions=result.get("interview_questions", []),
        networking_drafts=result.get("networking_drafts", {}),
        rag_cases=result.get("rag_cases", []),
        final_report=result.get("final_report", ""),
    )
