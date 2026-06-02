from typing import List, Optional

from pydantic import BaseModel, Field


class Education(BaseModel):
    undergrad_school: Optional[str] = None
    undergrad_tier: Optional[str] = None
    grad_school: Optional[str] = None
    grad_degree: Optional[str] = None
    grad_year: Optional[int] = None


class Experience(BaseModel):
    company: str
    type: Optional[str] = None
    sector: Optional[str] = None
    role: Optional[str] = None
    duration_months: Optional[int] = None
    key_output: List[str] = Field(default_factory=list)


class Skills(BaseModel):
    modeling: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    language: List[str] = Field(default_factory=list)
    sector_knowledge: List[str] = Field(default_factory=list)


class Target(BaseModel):
    city: List[str] = Field(default_factory=list)
    job_type: List[str] = Field(default_factory=list)
    sector: List[str] = Field(default_factory=list)
    timeline: Optional[str] = None


class DiagnosisSummary(BaseModel):
    match_score: Optional[int] = None
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    last_updated: Optional[str] = None


class CandidateProfile(BaseModel):
    candidate_id: str
    resume_raw: Optional[str] = None
    education: Optional[Education] = None
    experience: List[Experience] = Field(default_factory=list)
    skills: Optional[Skills] = None
    target: Optional[Target] = None
    diagnosis: Optional[DiagnosisSummary] = None
