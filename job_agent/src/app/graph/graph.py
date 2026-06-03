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


def build_graph() -> StateGraph:
    graph = StateGraph(InvestmentJobState)

    # ── nodes ──────────────────────────────────────────────────────────────
    graph.add_node("jd_scraper",          jd_scraper_agent)
    graph.add_node("jd_parser",           jd_parser_agent)
    graph.add_node("rag_retriever",       rag_agent)
    graph.add_node("candidate_diagnosis", diagnosis_agent)
    graph.add_node("resume_rewriter",     rewriter_agent)
    graph.add_node("cover_letter",        cover_letter_agent)
    graph.add_node("question_bank",       question_bank_agent)
    graph.add_node("interview_map",       interview_map_agent)
    graph.add_node("interview_trainer",   interview_agent)
    graph.add_node("resume_coach",        resume_coach_agent)
    graph.add_node("coaching_flow",       coaching_flow_agent)
    graph.add_node("networking_drafter",  networking_agent)
    graph.add_node("final_report",        report_generator_agent)

    # ── edges ──────────────────────────────────────────────────────────────
    graph.set_entry_point("jd_scraper")
    graph.add_edge("jd_scraper",          "jd_parser")
    graph.add_edge("jd_parser",           "rag_retriever")
    graph.add_edge("rag_retriever",       "candidate_diagnosis")
    graph.add_edge("candidate_diagnosis", "resume_rewriter")
    graph.add_edge("resume_rewriter",     "cover_letter")
    graph.add_edge("cover_letter",        "question_bank")
    graph.add_edge("question_bank",       "interview_map")
    graph.add_edge("interview_map",       "interview_trainer")
    graph.add_edge("interview_trainer",   "resume_coach")
    graph.add_edge("resume_coach",        "coaching_flow")
    graph.add_edge("coaching_flow",       "networking_drafter")
    graph.add_edge("networking_drafter",  "final_report")
    graph.add_edge("final_report",        END)

    return graph.compile()
