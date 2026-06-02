from __future__ import annotations

import re
from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def _extract_bullets(text: str, max_bullets: int = 5) -> List[str]:
    """
    Extract bullet-style lines from resume text.
    Accepts lines starting with -, •, *, or numbered lists.
    Falls back to the first `max_bullets` non-empty lines.
    """
    bullet_pat = re.compile(r"^[-•*]\s+|^\d+[.)\s]\s*")
    bullets = [
        bullet_pat.sub("", line).strip()
        for line in text.splitlines()
        if bullet_pat.match(line.strip()) and line.strip()
    ]
    if bullets:
        return bullets[:max_bullets]
    # fallback: first non-empty lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return lines[:max_bullets]


def rewriter_agent(state: InvestmentJobState) -> Dict[str, dict]:
    resume_text = state.get("resume_text", "")
    jd_profile = state.get("jd_profile", {})

    job_type = jd_profile.get("job_type", "equity research")
    city = jd_profile.get("city", "unknown")
    sector = jd_profile.get("sector", "generalist")
    hard_reqs = jd_profile.get("hard_requirements", [])

    # Rule-based fallback bullets so the agent returns something useful without LLM
    raw_bullets = _extract_bullets(resume_text)
    fallback_bullets = raw_bullets if raw_bullets else [
        "建议加入 2-3 条含量化指标的工作成果",
        "补充 stock pitch 关键词与行业眼光描述",
        "明确模型 / 估值经验，符合{sector}岂位需求".format(sector=sector),
    ]

    versions_fallback = {
        "sell_side_cn": fallback_bullets,
        "buy_side_bilingual": fallback_bullets,
        "hk_asset_mgmt_en": fallback_bullets,
    }

    prompt = f"""你是一位投研求职顾问。请将下面的简历改写为三个针对不同岗位的版本。

【候选人简历】
{resume_text}

【目标岗位信息】
- 类型：{job_type}，城市：{city}，行业：{sector}
- 核心要求：{hard_reqs}

请返回 JSON，包含以下三个字段，每个字段为 4-6 条 bullet 列表：

1. sell_side_cn：针对上海/香港卖方应展（中文）
   - 强调行业研究深度、公司调研结果、模型能力
   - 量化工作成果（如覆盖公司数/调研报告数）

2. buy_side_bilingual：针对公募/私募买方（中英混合）
   - 强调投资逻辑、仓位思考、风险感知、stock pitch 经验

3. hk_asset_mgmt_en：针对香港资管/外资机构（英文）
   - 强调双语能力、跨市场研究经验、ESG/quant 等加分项
不要自行添加简历里没有的内容，仅基于原文改写。
"""

    versions = generate_json(prompt, versions_fallback)
    return {"resume_versions": versions}
