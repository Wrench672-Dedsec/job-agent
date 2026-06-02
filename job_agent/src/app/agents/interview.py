from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def _questions_for(job_type: str) -> List[str]:
    if job_type == "buy-side":
        return [
            "Pitch one stock: thesis, catalyst, valuation, risks",
            "What is your bear case and stop-loss?",
            "Walk through a DCF you built",
            "How do you size a position?",
            "Industry view: top 2 tailwinds in your sector",
            "What is priced in by the market today?",
            "Explain a recent miss in your research",
            "Describe your data workflow for research",
            "Behavioral: why this fund?",
            "Behavioral: a time you changed your view",
        ]
    return [
        "Pitch one stock and defend your target price",
        "What is your catalyst for the next quarter?",
        "Build a quick valuation using comps",
        "Explain a revenue driver in your coverage",
        "Industry view: key competitive dynamics",
        "How do you prioritize coverage?",
        "Describe a report you wrote",
        "Walk through a model assumption",
        "Behavioral: why sell-side?",
        "Behavioral: describe a tough deadline",
    ]


def interview_agent(state: InvestmentJobState) -> Dict[str, List[str]]:
    job_type = state.get("jd_profile", {}).get("job_type", "unknown")
    questions = _questions_for(job_type)
    prompt = f"Generate 10 interview questions for a {job_type} equity research role. Return JSON with interview_questions list only."
    result = generate_json(prompt, {"interview_questions": questions})
    questions = result.get("interview_questions", questions)
    return {"interview_questions": questions}
