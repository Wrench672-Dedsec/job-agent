from typing import List, Optional

from pydantic import BaseModel, Field


class CaseCandidateProfile(BaseModel):
    education: Optional[str] = None
    sector_focus: Optional[str] = None
    prior_experience: Optional[str] = None
    weakness: Optional[str] = None


class CaseTargetJob(BaseModel):
    city: Optional[str] = None
    company_type: Optional[str] = None
    sector: Optional[str] = None


class CaseIntervention(BaseModel):
    resume_change: Optional[str] = None
    pitch_prep: Optional[str] = None
    networking: Optional[str] = None


class CaseRecord(BaseModel):
    case_id: Optional[str] = None
    source: Optional[str] = None
    authorized: Optional[bool] = None
    candidate_profile: Optional[CaseCandidateProfile] = None
    target_job: Optional[CaseTargetJob] = None
    problem_type: List[str] = Field(default_factory=list)
    intervention: Optional[CaseIntervention] = None
    outcome: Optional[str] = None
    timeline_weeks: Optional[int] = None
    key_insight: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    evidence_chunk: Optional[str] = None
