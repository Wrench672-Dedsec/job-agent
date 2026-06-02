from typing import Dict

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def _detect_sector(text: str) -> str:
    candidates = [
        "healthcare",
        "tmt",
        "macro",
        "semiconductor",
        "new energy",
        "generalist",
    ]
    for item in candidates:
        if item in text:
            return item
    return "generalist"


def _detect_city(text: str) -> str:
    if "hong kong" in text:
        return "Hong Kong"
    if "shanghai" in text:
        return "Shanghai"
    return "Unknown"


def _detect_job_type(text: str) -> str:
    if "buy-side" in text or "asset management" in text:
        return "buy-side"
    if "sell-side" in text or "equity research" in text or "securities" in text:
        return "sell-side"
    return "unknown"


def jd_parser_agent(state: InvestmentJobState) -> Dict[str, dict]:
    jd_text = state.get("jd_text", "")
    text = jd_text.lower()
    job_type = _detect_job_type(text)
    city = _detect_city(text)
    sector = _detect_sector(text)

    hard = []
    for key in ["model", "valuation", "research", "python", "excel", "bloomberg"]:
        if key in text:
            hard.append(key)
    if not hard:
        hard = ["research", "financial modeling", "industry knowledge"]

    profile = {
        "job_type": job_type,
        "city": city,
        "sector": sector,
        "hard_requirements": hard,
        "soft_requirements": ["bilingual", "prior internship"],
        "language_requirement": "bilingual" if "bilingual" in text else "unspecified",
        "interview_style": "stock pitch / technical / behavioral",
        "seniority": "unknown",
        "pitch_probability": 0.7,
        "model_test_probability": 0.5,
    }
    prompt = f"Parse this job description into JSON with keys job_type, city, sector, hard_requirements, soft_requirements, language_requirement, interview_style, seniority, pitch_probability, model_test_probability. JD: {jd_text}"
    profile = generate_json(prompt, profile)
    return {"jd_profile": profile}
