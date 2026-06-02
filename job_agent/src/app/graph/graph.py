from __future__ import annotations

from typing import Dict

from langgraph.graph import StateGraph, END

from app.graph.state import InvestmentJobState
from app.agents.jd_parser import jd_parser_agent
from app.agents.rag import rag_agent
from app.agents.diagnosis import diagnosis_agent
from app.agents.rewriter import rewriter_agent
from app.agents.interview import interview_agent
from app.agents.networking import networking_agent
from app.llm import generate_text


def final_report_agent(state: InvestmentJobState) -> Dict[str, str]:
    jd = state.get("jd_profile", {})
    dx = state.get("diagnosis", {})
    qs = state.get("interview_questions", [])
    versions = state.get("resume_versions", {})
    drafts = state.get("networking_drafts", {})

    # Build a structured prompt that asks the LLM to produce the final report
    prompt = (
        "请根据以下各模块输出，生成一份清晰的中文求职分析报告。"
        "报告应包含：岗位分析、候选人评估、简历改写建议、"
        "面试准备要点、下周行动计划。请使用 Markdown 格式。

"
        f"岗位信息：类型={jd.get('job_type')}，城市={jd.get('city')}，行业={jd.get('sector')}
"
        f"评估结果：匹配分={dx.get('match_score')}，"
        f"优势={dx.get('strengths')}，短板={dx.get('gaps')}
"
        f"首要改进项={dx.get('recommendation_priority')}
"
        f"面试题目（共 {len(qs)} 题，列出前 5 题）：{qs[:5]}
"
        f"简历版本关键字：{list(versions.keys())}
"
        f"沟通模板已生成：{list(drafts.keys())}
"
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
        f"## 面试题目（前 5 题）\n"
        + "\n".join(f"{i+1}. {q}" for i, q in enumerate(qs[:5]))
        + f"\n\n共 {len(qs)} 题已生成。"
    )

    report = generate_text(prompt, fallback=fallback)
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
