from typing import Dict

from langgraph.graph import StateGraph, END

from app.graph.state import InvestmentJobState
from app.agents.jd_parser import jd_parser_agent
from app.agents.rag import rag_agent
from app.agents.diagnosis import diagnosis_agent
from app.agents.rewriter import rewriter_agent
from app.agents.interview import interview_agent
from app.agents.networking import networking_agent


def final_report_agent(state: InvestmentJobState) -> Dict[str, str]:
    jd_profile = state.get("jd_profile", {})
    diagnosis = state.get("diagnosis", {})
    questions = state.get("interview_questions", [])
    report = (
        f"Job type: {jd_profile.get('job_type', 'unknown')}\n"
        f"City: {jd_profile.get('city', 'unknown')}\n"
        f"Sector: {jd_profile.get('sector', 'unknown')}\n"
        f"Match score: {diagnosis.get('match_score', 'n/a')}\n"
        f"Interview questions: {len(questions)}\n"
    )
    return {"final_report": report}


def build_graph() -> StateGraph:
    graph = StateGraph(InvestmentJobState)
    graph.add_node("jd_parser", jd_parser_agent)
    graph.add_node("rag_retriever", rag_agent)
    graph.add_node("candidate_diagnosis", diagnosis_agent)
    graph.add_node("resume_rewriter", rewriter_agent)
    graph.add_node("interview_trainer", interview_agent)
    graph.add_node("networking_drafter", networking_agent)
    graph.add_node("final_report", final_report_agent)

    graph.set_entry_point("jd_parser")
    graph.add_edge("jd_parser", "rag_retriever")
    graph.add_edge("rag_retriever", "candidate_diagnosis")
    graph.add_edge("candidate_diagnosis", "resume_rewriter")
    graph.add_edge("resume_rewriter", "interview_trainer")
    graph.add_edge("interview_trainer", "networking_drafter")
    graph.add_edge("networking_drafter", "final_report")
    graph.add_edge("final_report", END)

    return graph.compile()
