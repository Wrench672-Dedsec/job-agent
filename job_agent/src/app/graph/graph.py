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
from app.agents.interview import interview_agent
from app.agents.resume_coach import resume_coach_agent
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

    prompt = (
        "请根据以下各模块输出，生成一份完整的中文求职分析报告（Markdown 格式）。\n"
        "报告结构：\n"
        "1. 岗位分析摘要\n2. 候选人评估\n3. 简历改写要点\n"
        "4. Cover Letter 生成情况\n5. 面试题库摘要（技术面+行为面）\n"
        "6. 实习经历复盘要点\n7. Stock Pitch 练习框架\n"
        "8. 社交/内推沟通模板\n9. 下周行动计划（7天可落地）\n\n"
        f"JD 数量：{jd_count} 份已收集；Cover Letter：{cl_count} 份已生成\n"
        f"岗位：{jd.get('job_type')} | 城市：{jd.get('city')} | 行业：{jd.get('sector')}\n"
        f"匹配分：{dx.get('match_score')} | 优势：{dx.get('strengths')} | 短板：{dx.get('gaps')}\n"
        f"首要改进：{dx.get('recommendation_priority')}\n"
        f"题库：{bank_meta.get('total_questions', len(qs))} 道题\n"
        f"实习复盘：{drill_count} 段经历已生成追问题\n"
        f"简历版本：{list(versions.keys())}\n"
        f"沟通模板：{list(drafts.keys())}\n"
    )

    fallback = (
        f"# 求职分析报告\n\n"
        f"## 岗位信息\n"
        f"- 类型：{jd.get('job_type', 'unknown')}\n"
        f"- 城市：{jd.get('city', 'unknown')}\n"
        f"- 行业：{jd.get('sector', 'unknown')}\n\n"
        f"## 候选人评估\n"
        f"- 匹配度：{dx.get('match_score', 'n/a')}\n"
        f"- 优势：{dx.get('strengths', [])}\n"
        f"- 短板：{dx.get('gaps', [])}\n"
        f"- 首要改进：{dx.get('recommendation_priority', '')}\n\n"
        f"## 已生成内容摘要\n"
        f"- JD 收集：{jd_count} 份\n"
        f"- Cover Letter：{cl_count} 份\n"
        f"- 面试题：{bank_meta.get('total_questions', len(qs))} 道\n"
        f"- 实习复盘：{drill_count} 段\n"
        f"- 简历版本：{list(versions.keys())}\n"
    )

    report = generate_text(prompt, fallback=fallback)
    return {"final_report": report}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    graph = StateGraph(InvestmentJobState)

    # ── nodes ───────────────────────────────────────────────────────────────
    graph.add_node("jd_scraper",        jd_scraper_agent)
    graph.add_node("jd_parser",         jd_parser_agent)
    graph.add_node("rag_retriever",     rag_agent)
    graph.add_node("candidate_diagnosis", diagnosis_agent)
    graph.add_node("resume_rewriter",   rewriter_agent)
    graph.add_node("cover_letter",      cover_letter_agent)
    graph.add_node("question_bank",     question_bank_agent)
    graph.add_node("interview_trainer", interview_agent)
    graph.add_node("resume_coach",      resume_coach_agent)
    graph.add_node("networking_drafter", networking_agent)
    graph.add_node("final_report",      final_report_agent)

    # ── edges (linear pipeline) ─────────────────────────────────────────────
    # JD collection & parsing
    graph.set_entry_point("jd_scraper")
    graph.add_edge("jd_scraper",          "jd_parser")

    # RAG retrieval needs parsed JD profile
    graph.add_edge("jd_parser",           "rag_retriever")

    # Diagnosis needs RAG cases + JD profile
    graph.add_edge("rag_retriever",       "candidate_diagnosis")

    # Resume rewriting and cover letter can run after diagnosis
    graph.add_edge("candidate_diagnosis", "resume_rewriter")
    graph.add_edge("resume_rewriter",     "cover_letter")

    # Question bank and interview questions
    graph.add_edge("cover_letter",        "question_bank")
    graph.add_edge("question_bank",       "interview_trainer")

    # Resume coaching (internship recall + pitch scaffold)
    graph.add_edge("interview_trainer",   "resume_coach")

    # Networking drafts
    graph.add_edge("resume_coach",        "networking_drafter")

    # Final report
    graph.add_edge("networking_drafter",  "final_report")
    graph.add_edge("final_report",        END)

    return graph.compile()
