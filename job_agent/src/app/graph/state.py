from typing import List, TypedDict


class InvestmentJobState(TypedDict, total=False):
    resume_text: str
    jd_text: str
    target_city: str
    target_sector: str
    jd_profile: dict
    diagnosis: dict
    resume_versions: dict
    interview_questions: List[str]
    mock_answers: List[str]
    scores: dict
    networking_drafts: dict
    rag_cases: List[dict]
    final_report: str
