from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def _score_resume(resume_text: str, sector: str) -> int:
    text = resume_text.lower()
    score = 50
    if sector and sector in text:
        score += 10
    for key in ["python", "model", "valuation", "research"]:
        if key in text:
            score += 10
    return min(score, 100)


def diagnosis_agent(state: InvestmentJobState) -> Dict[str, dict]:
    resume_text = state.get("resume_text", "")
    jd_profile = state.get("jd_profile", {})
    sector = jd_profile.get("sector", "")
    score = _score_resume(resume_text, sector)

    strengths: List[str] = []
    if "python" in resume_text.lower():
        strengths.append("Data skills: Python in research workflow")
    if "model" in resume_text.lower():
        strengths.append("Modeling: exposure to valuation or forecasting")
    if not strengths:
        strengths.append("Research exposure: expand with concrete outputs")

    gaps = [
        "Quantify impact with metrics",
        "Clarify stock pitch and catalysts",
        "Add evidence of sector coverage",
    ]

    diagnosis = {
        "match_score": score,
        "strengths": strengths,
        "gaps": gaps,
        "recommendation_priority": "Prepare a clear stock pitch with valuation and risks",
    }
    prompt = f"Diagnose this candidate for a job. Resume: {resume_text}. JD profile: {jd_profile}. Return JSON with match_score, strengths, gaps, recommendation_priority."
    diagnosis = generate_json(prompt, diagnosis)
    return {"diagnosis": diagnosis}
