from __future__ import annotations

from typing import Dict

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
from app.agents.coaching_flow import coaching_flow_agent   # NEW
from app.agents.networking import networking_agent
from app.llm import generate_text


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------

def final_report_agent(state: InvestmentJobState) -> Dict[str, str]:
    jd = state.get("jd_profile") or {}
    dx = state.get("diagnosis") or {}
    qs = state.get("interview_questions") or []
    versions = state.get("resume_versions") or {}
    drafts = state.get("networking_drafts") or {}
    bank_meta = (state.get("question_bank") or {}).get("meta", {})
    cl_count = len(state.get("cover_letters") or [])
    jd_count = len(state.get("collected_jds") or [])
    coaching = state.get("coaching_session") or {}
    drill_count = len(coaching.get("internship_drills") or [])

    # interview_map summary
    imap = state.get("interview_map") or {}
    mock_plan = imap.get("mock_plan") or {}
    map_summary = (
        f"\u9762\u8bd5\u5730\u56fe\uff1a{len(imap.get('rounds', []))} \u8f6e | "
        f"\u603b\u9898\u91cf {mock_plan.get('total_questions', 0)} \u9053 | "
        f"\u9884\u8ba1 {mock_plan.get('estimated_minutes', 0)} \u5206\u949f\n"
        f"\u8f6e\u6b21\uff1a{' \u2192 '.join(mock_plan.get('session_order', []))}\n"
        f"coaching tips\uff1a{imap.get('coaching_tips', '')}"
    )

    # coaching_flow summary
    cf = state.get("coaching_flow") or {}
    prog = cf.get("overall_progress") or {}
    weekly = cf.get("weekly_plan") or {}
    cf_summary = (
        f"Coaching Flow: {prog.get('completed', 0)}/{prog.get('total_phases', 4)} phases "
        f"({prog.get('pct', 0)}%)\n"
        f"Next action: {cf.get('next_action', '')}\n"
        f"7\u5929\u91cc\u7a0b\u7891\uff1a{weekly.get('key_milestones', [])}"
    )

    prompt = (
        "\u8bf7\u6839\u636e\u4ee5\u4e0b\u5404\u6a21\u5757\u8f93\u51fa\uff0c\u751f\u6210\u4e00\u4efd\u5b8c\u6574\u7684\u4e2d\u6587\u6c42\u804c\u5206\u6790\u62a5\u544a\uff08Markdown \u683c\u5f0f\uff09\u3002\n"
        "\u62a5\u544a\u7ed3\u6784\uff1a\n"
        "1. \u5c97\u4f4d\u5206\u6790\u6458\u8981\n2. \u5019\u9009\u4eba\u8bc4\u4f30\n3. \u7b80\u5386\u6539\u5199\u8981\u70b9\n"
        "4. Cover Letter \u751f\u6210\u60c5\u51b5\n5. \u9762\u8bd5\u5730\u56fe\uff08\u8f6e\u6b21 + \u6838\u5fc3\u9898\u7ec4 + \u8ffd\u95ee\u6846\u67b6\uff09\n"
        "6. \u9898\u5e93\u6458\u8981\uff08\u6280\u672f\u9762+\u884c\u4e3a\u9762\uff09\n"
        "7. \u5b9e\u4e60\u7ecf\u5386\u590d\u76d8\u8981\u70b9\n8. Stock Pitch \u7ec3\u4e60\u6846\u67b6\n"
        "9. Coaching Flow \u9636\u6bb5\u8ba1\u5212 + 7 \u5929\u884c\u52a8\u8ba1\u5212\n"
        "10. \u793e\u4ea4/\u5185\u63a8\u6c9f\u901a\u6a21\u677f\n\n"
        f"JD \u6570\u91cf\uff1a{jd_count} \u4efd\uff1bCover Letter\uff1a{cl_count} \u4efd\n"
        f"\u5c97\u4f4d\uff1a{jd.get('job_type')} | \u57ce\u5e02\uff1a{jd.get('city')} | \u884c\u4e1a\uff1a{jd.get('sector')}\n"
        f"\u5339\u914d\u5206\uff1a{dx.get('match_score')} | \u4f18\u52bf\uff1a{dx.get('strengths')} | \u77ed\u677f\uff1a{dx.get('gaps')}\n"
        f"\u9996\u8981\u6539\u8fdb\uff1a{dx.get('recommendation_priority')}\n"
        f"\u9898\u5e93\uff1a{bank_meta.get('total_questions', len(qs))} \u9053\u9898\n"
        f"{map_summary}\n"
        f"{cf_summary}\n"
        f"\u5b9e\u4e60\u590d\u76d8\uff1a{drill_count} \u6bb5\n"
        f"\u7b80\u5386\u7248\u672c\uff1a{list(versions.keys())}\n"
        f"\u6c9f\u901a\u6a21\u677f\uff1a{list(drafts.keys())}\n"
    )

    fallback = (
        f"# \u6c42\u804c\u5206\u6790\u62a5\u544a\n\n"
        f"## \u5c97\u4f4d\u4fe1\u606f\n"
        f"- \u7c7b\u578b\uff1a{jd.get('job_type', 'unknown')}\n"
        f"- \u57ce\u5e02\uff1a{jd.get('city', 'unknown')}\n"
        f"- \u884c\u4e1a\uff1a{jd.get('sector', 'unknown')}\n\n"
        f"## \u5019\u9009\u4eba\u8bc4\u4f30\n"
        f"- \u5339\u914d\u5ea6\uff1a{dx.get('match_score', 'n/a')}\n"
        f"- \u4f18\u52bf\uff1a{dx.get('strengths', [])}\n"
        f"- \u77ed\u677f\uff1a{dx.get('gaps', [])}\n"
        f"- \u9996\u8981\u6539\u8fdb\uff1a{dx.get('recommendation_priority', '')}\n\n"
        f"## \u9762\u8bd5\u5730\u56fe\n{map_summary}\n\n"
        f"## Coaching Flow\n{cf_summary}\n\n"
        f"## \u5df2\u751f\u6210\u5185\u5bb9\u6458\u8981\n"
        f"- JD \u6536\u96c6\uff1a{jd_count} \u4efd\n"
        f"- Cover Letter\uff1a{cl_count} \u4efd\n"
        f"- \u9762\u8bd5\u9898\uff1a{bank_meta.get('total_questions', len(qs))} \u9053\n"
        f"- \u5b9e\u4e60\u590d\u76d8\uff1a{drill_count} \u6bb5\n"
        f"- \u7b80\u5386\u7248\u672c\uff1a{list(versions.keys())}\n"
    )

    report = generate_text(prompt, fallback=fallback)
    return {"final_report": report}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(InvestmentJobState)

    # ── nodes ────────────────────────────────────────────────────────────────
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
    graph.add_node("coaching_flow",       coaching_flow_agent)   # NEW
    graph.add_node("networking_drafter",  networking_agent)
    graph.add_node("final_report",        final_report_agent)

    # ── edges ─────────────────────────────────────────────────────────────────
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
    graph.add_edge("resume_coach",        "coaching_flow")       # NEW
    graph.add_edge("coaching_flow",       "networking_drafter")  # NEW
    graph.add_edge("networking_drafter",  "final_report")
    graph.add_edge("final_report",        END)

    return graph.compile()
