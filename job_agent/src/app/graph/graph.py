from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.graph.state import InvestmentJobState
from app.agents.jd_scraper import jd_scraper_agent
from app.agents.jd_parser import jd_parser_agent
from app.agents.rag import rag_agent
from app.agents.diagnosis import diagnosis_agent
from app.agents.rewriter import rewriter_agent
from app.agents.cover_letter import cover_letter_agent
from app.agents.question_bank import question_bank_agent
from app.agents.interview_map import interview_map_agent
from app.agents.interview import interview_agent
from app.agents.resume_coach import resume_coach_agent
from app.agents.coaching_flow import coaching_flow_agent
from app.agents.networking import networking_agent
from app.agents.report_generator import report_generator_agent


# ── routing helpers ────────────────────────────────────────────────────────────

def _route_after_scraper(state: InvestmentJobState) -> str:
    """Skip jd_parser when no JDs were collected (e.g. manual jd_text only)."""
    collected = state.get("collected_jds") or []
    jd_text = state.get("jd_text", "").strip()
    if collected or jd_text:
        return "jd_parser"
    return "rag_retriever"


def _route_after_diagnosis(state: InvestmentJobState) -> str:
    """
    High match score (>=70) → go straight to rewriter.
    Low match score        → resume_coach first for gap-filling drills.
    """
    diagnosis = state.get("diagnosis") or {}
    match_score = diagnosis.get("match_score", 0)
    if match_score >= 70:
        return "resume_rewriter"
    return "resume_coach"


def _route_after_resume_coach(state: InvestmentJobState) -> str:
    """After coaching session, always continue to rewriter."""
    return "resume_rewriter"


def _route_after_rewriter(state: InvestmentJobState) -> str:
    """Always generate cover letters after resume rewrite."""
    return "cover_letter"


def _route_after_cover_letter(state: InvestmentJobState) -> str:
    """Always build question bank after cover letter."""
    return "question_bank"


def _route_after_question_bank(state: InvestmentJobState) -> str:
    """Build interview map before running mock interview."""
    return "interview_map"


def _route_after_interview_map(state: InvestmentJobState) -> str:
    """Run mock interview trainer."""
    return "interview_trainer"


def _route_after_interview(state: InvestmentJobState) -> str:
    """Build coaching flow plan after interview trainer."""
    return "coaching_flow"


def _route_after_coaching_flow(state: InvestmentJobState) -> str:
    """Generate networking drafts after coaching flow."""
    return "networking"


def _route_after_networking(state: InvestmentJobState) -> str:
    """Final step: generate consolidated report."""
    return "report_generator"


# ── graph builder ──────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(InvestmentJobState)

    # ── nodes ──────────────────────────────────────────────────────────────────
    graph.add_node("jd_scraper",          jd_scraper_agent)
    graph.add_node("jd_parser",           jd_parser_agent)
    graph.add_node("rag_retriever",       rag_agent)
    graph.add_node("candidate_diagnosis", diagnosis_agent)
    graph.add_node("resume_coach",        resume_coach_agent)
    graph.add_node("resume_rewriter",     rewriter_agent)
    graph.add_node("cover_letter",        cover_letter_agent)
    graph.add_node("question_bank",       question_bank_agent)
    graph.add_node("interview_map",       interview_map_agent)
    graph.add_node("interview_trainer",   interview_agent)
    graph.add_node("coaching_flow",       coaching_flow_agent)
    graph.add_node("networking",          networking_agent)
    graph.add_node("report_generator",    report_generator_agent)

    # ── entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("jd_scraper")

    # ── edges ──────────────────────────────────────────────────────────────────
    # jd_scraper → jd_parser (conditional: skip if no JDs collected)
    graph.add_conditional_edges(
        "jd_scraper",
        _route_after_scraper,
        {
            "jd_parser":     "jd_parser",
            "rag_retriever": "rag_retriever",
        },
    )

    # jd_parser → rag_retriever (always)
    graph.add_edge("jd_parser", "rag_retriever")

    # rag_retriever → candidate_diagnosis (always)
    graph.add_edge("rag_retriever", "candidate_diagnosis")

    # candidate_diagnosis → resume_coach OR resume_rewriter
    graph.add_conditional_edges(
        "candidate_diagnosis",
        _route_after_diagnosis,
        {
            "resume_coach":    "resume_coach",
            "resume_rewriter": "resume_rewriter",
        },
    )

    # resume_coach → resume_rewriter (always)
    graph.add_edge("resume_coach", "resume_rewriter")

    # resume_rewriter → cover_letter (always)
    graph.add_edge("resume_rewriter", "cover_letter")

    # cover_letter → question_bank (always)
    graph.add_edge("cover_letter", "question_bank")

    # question_bank → interview_map (always)
    graph.add_edge("question_bank", "interview_map")

    # interview_map → interview_trainer (always)
    graph.add_edge("interview_map", "interview_trainer")

    # interview_trainer → coaching_flow (always)
    graph.add_edge("interview_trainer", "coaching_flow")

    # coaching_flow → networking (always)
    graph.add_edge("coaching_flow", "networking")

    # networking → report_generator (always)
    graph.add_edge("networking", "report_generator")

    # report_generator → END
    graph.add_edge("report_generator", END)

    return graph


# ── compiled singleton ─────────────────────────────────────────────────────────
compiled_graph = build_graph().compile()
