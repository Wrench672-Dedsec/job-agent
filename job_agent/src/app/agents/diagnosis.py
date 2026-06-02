from __future__ import annotations

import json
from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def _format_rag_cases(cases: List[dict]) -> str:
    """Serialise the top RAG cases into a compact string for the prompt."""
    if not cases:
        return "No reference cases available."
    snippets = []
    for i, c in enumerate(cases[:3], 1):
        # Accept any key names the JSON might use
        bg = c.get("background") or c.get("candidate_background") or ""
        result = c.get("result") or c.get("outcome") or ""
        tip = c.get("key_lesson") or c.get("recommendation") or ""
        snippets.append(f"Case {i}: {bg} | result: {result} | lesson: {tip}")
    return "\n".join(snippets)


def diagnosis_agent(state: InvestmentJobState) -> Dict[str, dict]:
    resume_text = state.get("resume_text", "")
    jd_profile = state.get("jd_profile", {})
    rag_cases = state.get("rag_cases", [])

    case_context = _format_rag_cases(rag_cases)

    prompt = f"""你是一位专业投研求职顾问，熊猫两市场（香港外资买方/卖方、上海内资公募私募）均有深度了解。

【候选人简历】
{resume_text}

【目标岗位信息】
- 岗位类型：{jd_profile.get('job_type', 'unknown')}
- 城市：{jd_profile.get('city', 'unknown')}
- 覆盖行业：{jd_profile.get('sector', 'unknown')}
- 硬性要求：{jd_profile.get('hard_requirements', [])}
- 语言要求：{jd_profile.get('language_requirement', 'unspecified')}

【参考案例（同类候选人经历）】
{case_context}

请小心评估，返回以下 JSON：
{{
  "match_score": 0-100整数（基于内容匹配，不是关键词计数）,
  "strengths": [最多3条具体优势，应引用简历原文作为证据],
  "gaps": [最多3条具体短板，说明为什么是短板而非写固定话术],
  "recommendation_priority": "优先级最高的一个改进动作，7天内可落地"
}}
"""

    fallback: dict = {
        "match_score": 50,
        "strengths": ["请提供更详细的简历信息"],
        "gaps": ["简历内容不足，无法完成评估"],
        "recommendation_priority": "完善简历后重试",
    }
    diagnosis = generate_json(prompt, fallback)
    return {"diagnosis": diagnosis}
