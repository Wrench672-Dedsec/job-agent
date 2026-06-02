from typing import List, Optional

from pydantic import BaseModel, Field


class JDProfile(BaseModel):
    job_type: Optional[str] = None
    city: Optional[str] = None
    sector: Optional[str] = None
    hard_requirements: List[str] = Field(default_factory=list)
    soft_requirements: List[str] = Field(default_factory=list)
    language_requirement: Optional[str] = None
    interview_style: Optional[str] = None
    seniority: Optional[str] = None
    pitch_probability: Optional[float] = None
    model_test_probability: Optional[float] = None


class Diagnosis(BaseModel):
    match_score: Optional[int] = None
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendation_priority: Optional[str] = None


class ResumeVersions(BaseModel):
    sell_side_cn: List[str] = Field(default_factory=list)
    buy_side_bilingual: List[str] = Field(default_factory=list)
    hk_asset_mgmt_en: List[str] = Field(default_factory=list)


class NetworkingDrafts(BaseModel):
    referral_email_cn: Optional[str] = None
    linkedin_dm_en: Optional[str] = None
    thank_you_en: Optional[str] = None


class RunRequest(BaseModel):
    resume_text: str
    jd_text: str
    target_city: Optional[str] = None
    target_sector: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class RunResponse(BaseModel):
    jd_profile: dict
    diagnosis: dict
    resume_versions: dict
    interview_questions: List[str] = Field(default_factory=list)
    networking_drafts: dict
    rag_cases: List[dict] = Field(default_factory=list)
    final_report: str
