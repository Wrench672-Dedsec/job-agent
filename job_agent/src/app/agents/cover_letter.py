from __future__ import annotations

"""Cover Letter Agent

Generates a tailored cover letter for each collected JD.
Also generates a targeted resume bullet patch (delta bullets) that
highlights the most relevant experience for that specific JD.

Outputs:
    cover_letters — list[dict] each with:
        source_url, company, title, cover_letter_cn, cover_letter_en,
        resume_patch (list[str] of targeted bullets for this JD)
"""

import logging
from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState

logger = logging.getLogger(__name__)


def _build_prompt(resume_text: str, jd: dict, diagnosis: dict) -> str:
    strengths = diagnosis.get("strengths", [])
    gaps = diagnosis.get("gaps", [])
    return f"""你是一位专业投研求职顾问，请针对以下 JD 生成一份 cover letter 和简历补丁。

【候选人简历】
{resume_text[:2000]}

【目标 JD】
公司：{jd.get('company', 'unknown')}
职位：{jd.get('title', 'unknown')}
城市：{jd.get('city', 'unknown')}
JD 正文（前1500字）：
{jd.get('raw_text', '')[:1500]}

【候选人诊断】
优势：{strengths}
短板：{gaps}

请返回 JSON，包含以下字段：
{{
  "cover_letter_cn": "中文 cover letter（300-400字），三段式：
    第一段：与 JD 最匹配的 1-2 项核心经历；
    第二段：针对 JD 具体要求的技能/行业理解；
    第三段：求职动机与对机构的具体了解",
  "cover_letter_en": "English cover letter (250-350 words), same three-section structure",
  "resume_patch": [
    "针对此 JD 最相关的 3-4 条简历 bullet，量化表达，直接可粘贴"
  ]
}}
不要编造简历中没有的经历。只基于候选人原始简历改写和强调。
"""


def cover_letter_agent(state: InvestmentJobState) -> Dict[str, List[dict]]:
    resume_text = state.get("resume_text") or ""
    diagnosis = state.get("diagnosis") or {}
    collected_jds: List[dict] = state.get("collected_jds") or []

    # If no collected JDs, fall back to single jd_text + jd_profile
    if not collected_jds:
        jd_profile = state.get("jd_profile") or {}
        collected_jds = [{
            "title": jd_profile.get("job_type", "analyst"),
            "company": "unknown",
            "city": jd_profile.get("city", "unknown"),
            "source_url": "manual",
            "raw_text": state.get("jd_text") or "",
        }]

    results: List[dict] = []
    for jd in collected_jds[:6]:  # cap at 6 to control API cost
        fallback = {
            "cover_letter_cn": "（LLM 未响应，请手动填写）",
            "cover_letter_en": "(LLM unavailable — please fill in manually.)",
            "resume_patch": ["Add 2-3 quantified bullets relevant to this JD"],
        }
        prompt = _build_prompt(resume_text, jd, diagnosis)
        output = generate_json(prompt, fallback)
        results.append({
            "source_url": jd.get("source_url", ""),
            "company": jd.get("company", "unknown"),
            "title": jd.get("title", "unknown"),
            "cover_letter_cn": output.get("cover_letter_cn", fallback["cover_letter_cn"]),
            "cover_letter_en": output.get("cover_letter_en", fallback["cover_letter_en"]),
            "resume_patch": output.get("resume_patch", fallback["resume_patch"]),
        })

    logger.info("cover_letter_agent: generated %d letters.", len(results))
    return {"cover_letters": results}
