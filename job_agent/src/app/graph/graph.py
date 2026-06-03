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
    # jd_scraper → jd_parser OR rag_retriever (skip parser if no JD input)
    graph.add_conditional_edges(
        "jd_scraper",
        _route_after_scraper,
        {
            "jd_parser":     "jd_parser",
            "rag_retriever": "rag_retriever",
        },
    )

    # jd_parser → rag_retriever
    graph.add_edge("jd_parser", "rag_retriever")

    # rag_retriever → candidate_diagnosis
    # diagnosis writes gaps/strengths into state; downstream agents read it.
    # It is purely diagnostic — it does NOT gate the pipeline.
    graph.add_edge("rag_retriever", "candidate_diagnosis")

    # candidate_diagnosis → resume_coach
    # resume_coach reads diagnosis.gaps to generate targeted drills.
    # Every candidate goes through coaching regardless of score.
    graph.add_edge("candidate_diagnosis", "resume_coach")

    # resume_coach → resume_rewriter
    graph.add_edge("resume_coach", "resume_rewriter")

    # resume_rewriter → cover_letter
    graph.add_edge("resume_rewriter", "cover_letter")

    # cover_letter → question_bank
    graph.add_edge("cover_letter", "question_bank")

    # question_bank → interview_map
    graph.add_edge("question_bank", "interview_map")

    # interview_map → interview_trainer
    graph.add_edge("interview_map", "interview_trainer")

    # interview_trainer → coaching_flow
    graph.add_edge("interview_trainer", "coaching_flow")

    # coaching_flow → networking
    graph.add_edge("coaching_flow", "networking")

    # networking → report_generator
    graph.add_edge("networking", "report_generator")

    # report_generator → END
    graph.add_edge("report_generator", END)

    return graph


# ── compiled singleton ─────────────────────────────────────────────────────────
compiled_graph = build_graph().compile()
