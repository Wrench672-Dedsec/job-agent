from __future__ import annotations

from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState


_QUESTIONS: dict[str, dict[str, List[str]]] = {
    "buy-side": {
        "default": [
            "Pitch one stock: thesis, catalyst, valuation, risks.",
            "What is your bear case and your stop-loss trigger?",
            "Walk through a DCF you built from scratch.",
            "How do you size a position? What is your max single-name weight?",
            "Name the top two tailwinds in your sector over the next 12 months.",
            "What does the market currently have wrong about this stock?",
            "Describe a research call where you were wrong. What did you change?",
            "Walk me through your weekly data workflow for tracking your names.",
            "Why this fund specifically over other long/short equity funds?",
            "Tell me about a time you changed your investment view under pressure.",
        ],
        "healthcare": [
            "What NMPA / FDA catalysts are you tracking this quarter?",
            "How do you model a drug royalty stream under different peak-sales scenarios?",
        ],
        "tmt": [
            "How do you value a SaaS company with negative earnings in China?",
            "What is your read on AI capital-expenditure cycle and its implications for semis?",
        ],
        "new energy": [
            "How do you model lithium carbonate price sensitivity in a battery cell manufacturer?",
            "What is your framework for shorting overcapacity plays in solar?",
        ],
    },
    "sell-side": {
        "default": [
            "Pitch one stock and defend your 12-month target price.",
            "What is your near-term catalyst and earnings revision direction?",
            "Build a quick EV/EBITDA comps table for your coverage universe.",
            "Walk through the key revenue driver model for a company you cover.",
            "Describe the competitive dynamics in your sector right now.",
            "How do you prioritise initiation coverage when you join a new desk?",
            "Walk me through a note you wrote: structure, key call, market reaction.",
            "Which model assumption do clients push back on most?",
            "Why sell-side research over buy-side or IBD?",
            "Describe a deadline you almost missed and how you managed it.",
        ],
    },
}


def _base_questions(job_type: str, sector: str) -> List[str]:
    bucket = _QUESTIONS.get(job_type, _QUESTIONS["sell-side"])
    questions: List[str] = list(bucket["default"])
    sector_qs = bucket.get(sector, [])
    # Replace last two defaults with sector-specific questions if available
    if sector_qs:
        questions = questions[:-2] + sector_qs
    return questions


def interview_agent(state: InvestmentJobState) -> Dict[str, List[str]]:
    jd_profile = state.get("jd_profile", {})
    job_type = jd_profile.get("job_type", "sell-side")
    sector = jd_profile.get("sector", "generalist")
    city = jd_profile.get("city", "unknown")
    hard_reqs = jd_profile.get("hard_requirements", [])

    fallback_questions = _base_questions(job_type, sector)

    prompt = (
        f"为以下岗位生成 10 道面试题："
        f"岗位类型={job_type}，行业={sector}，城市={city}，"
        f"硬性要求={hard_reqs}。"
        f"前 7 题为技术题（包含 stock pitch/model/valuation），"
        f"后 3 题为 behavioral。"
        f"题目要具体可执行，避免泛泛而谈。"
        f"返回 JSON: {{\"interview_questions\": [列表]}}。"
    )

    result = generate_json(prompt, {"interview_questions": fallback_questions})
    questions = result.get("interview_questions", fallback_questions)
    return {"interview_questions": questions}
