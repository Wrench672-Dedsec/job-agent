from __future__ import annotations

"""Resume Coach Agent

Helps the candidate recall and articulate their past internship experience
through a structured Q&A flow. Especially useful for stock pitch preparation.

Mode 1 — Internship Recall (auto, runs in graph):
  Parses resume for internship entries and generates targeted recall questions
  for each experience. Questions probe: what did you actually do, what data
  did you use, what was your conclusion, and what would you say differently now.

Mode 2 — Stock Pitch Builder (interactive, called directly):
  Given a ticker + basic info, generates a structured pitch scaffold and
  follow-up drill questions the candidate can practice answering.

Both modes write to state["coaching_session"].
"""

import logging
import re
from typing import Dict, List

from app.llm import generate_json, generate_text
from app.graph.state import InvestmentJobState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internship recall
# ---------------------------------------------------------------------------

def _extract_internship_blocks(resume_text: str) -> List[str]:
    """
    Heuristic extractor: split resume into blocks around internship keywords.
    Returns up to 5 blocks.
    """
    keywords = ["实习", "intern", "internship", "研究助理", "research assistant",
                "analyst intern", "summer", "兼职"]
    lines = resume_text.splitlines()
    blocks: List[str] = []
    current: List[str] = []

    for line in lines:
        low = line.lower()
        is_header = any(kw in low for kw in keywords)
        # New block starts at a keyword-header line
        if is_header and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    # Filter to blocks that actually look like experience (>20 chars)
    blocks = [b for b in blocks if len(b.strip()) > 20]
    return blocks[:5]


def _recall_questions_for_block(block: str, job_type: str) -> List[dict]:
    prompt = f"""
你是一位投研求职教练。以下是候选人简历中的一段实习经历描述：

{block[:800]}

请生成 5 道「重温追问」题，帮助候选人在面试中更好地表达这段经历。
要求：
1. 每道题针对这段描述中的具体内容（不要泛化）
2. 涵盖：做了什么→用了什么数据/方法→结论/建议→如果重来会怎么做→如何量化影响
3. 如果涉及股票/行业研究，加一道「如果在面试中被问到这个项目，你的 30 秒 pitch 是什么」

岗位类型：{job_type}

返回 JSON：{{"questions": [{{"question": str, "hint": str}}]}}
"""
    fallback = {"questions": [
        {"question": "这段实习中你独立完成了哪些具体分析工作？",
         "hint": "描述具体任务而非职责"},
        {"question": "你用了哪些数据源和工具？",
         "hint": "Bloomberg / Wind / Python / Excel 等"},
        {"question": "你的分析得出了什么结论？有没有被采用？",
         "hint": "量化影响最好"},
        {"question": "如果现在重新做这个项目，你会改进什么？",
         "hint": "展示反思能力"},
        {"question": "用一两句话向面试官 pitch 这段经历的亮点。",
         "hint": "简洁、有数据、有结论"},
    ]}
    result = generate_json(prompt, fallback)
    return result.get("questions", fallback["questions"])


# ---------------------------------------------------------------------------
# Stock pitch builder
# ---------------------------------------------------------------------------

def _build_pitch_scaffold(
    ticker: str, company_name: str, sector: str, job_type: str
) -> dict:
    prompt = f"""
你是投研面试教练。请为以下股票生成一个结构化的 pitch 练习框架，供候选人填写和练习。

股票代码：{ticker}
公司名称：{company_name}
行业：{sector}
岗位类型（买方/卖方）：{job_type}

请返回 JSON，包含以下字段：
{{
  "pitch_template": {{
    "one_line_thesis": "一句话投资逻辑（待候选人填写示范）",
    "key_drivers": ["三个关键驱动因素（每个附说明）"],
    "valuation": "估值方法和目标价区间",
    "bull_case": "多头情景假设",
    "bear_case": "空头情景假设",
    "catalysts": ["未来3-6个月可验证的催化剂"],
    "risks": ["前两大风险及应对"]
  }},
  "drill_questions": [
    "5道针对此 pitch 的追问题，逐步加深难度"
  ]
}}
如果不了解该公司，请基于行业通用逻辑生成框架，并注明需要候选人用真实数据填充。
"""
    fallback = {
        "pitch_template": {
            "one_line_thesis": f"{company_name} is a [long/short] because [key thesis].",
            "key_drivers": ["Driver 1: ", "Driver 2: ", "Driver 3: "],
            "valuation": f"Target: [X]x EV/EBITDA or [Y]x P/E implies [Z]% upside",
            "bull_case": "If [assumption], stock could reach [price].",
            "bear_case": "If [risk materializes], stock could fall to [price].",
            "catalysts": ["Q[X] earnings beat", "Regulatory approval"],
            "risks": ["Risk 1 + mitigant", "Risk 2 + mitigant"],
        },
        "drill_questions": [
            "What's your one-line investment thesis?",
            "What's your target price and methodology?",
            "What's the bear case and your stop-loss?",
            "What does the market currently have wrong?",
            "What's the next 90-day catalyst you'd monitor?",
        ],
    }
    return generate_json(prompt, fallback)


# ---------------------------------------------------------------------------
# Public agent (graph mode)
# ---------------------------------------------------------------------------

def resume_coach_agent(state: InvestmentJobState) -> Dict[str, dict]:
    resume_text = state.get("resume_text") or ""
    jd_profile = state.get("jd_profile") or {}
    job_type = jd_profile.get("job_type", "equity research")
    sector = jd_profile.get("sector", "generalist")

    blocks = _extract_internship_blocks(resume_text)

    internship_drills: List[dict] = []
    for i, block in enumerate(blocks):
        questions = _recall_questions_for_block(block, job_type)
        internship_drills.append({
            "internship_index": i + 1,
            "excerpt": block[:200],
            "recall_questions": questions,
        })

    # Generate a generic stock pitch scaffold for the target sector
    # (candidate can customise with a real ticker later)
    pitch_scaffold = _build_pitch_scaffold(
        ticker="[TICKER]",
        company_name=f"[{sector.upper()} COMPANY]",
        sector=sector,
        job_type=job_type,
    )

    coaching_session = {
        "internship_drills": internship_drills,
        "pitch_scaffold": pitch_scaffold,
        "usage_note": (
            "internship_drills: 针对每段实习的追问题，建议逐题回答后对照 hint 自评。\n"
            "pitch_scaffold: 填入真实 ticker 后用 resume_coach.build_pitch_for_ticker() "
            "获取针对性追问题。"
        ),
    }

    logger.info(
        "resume_coach_agent: %d internship blocks processed.",
        len(internship_drills),
    )
    return {"coaching_session": coaching_session}


# ---------------------------------------------------------------------------
# Standalone helper (call directly, not via graph)
# ---------------------------------------------------------------------------

def build_pitch_for_ticker(
    ticker: str,
    company_name: str,
    sector: str = "generalist",
    job_type: str = "buy-side",
) -> dict:
    """Call this directly to generate a pitch scaffold for a specific stock."""
    return _build_pitch_scaffold(ticker, company_name, sector, job_type)
