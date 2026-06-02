from typing import List, Optional

from pydantic import BaseModel, Field


class JDPosting(BaseModel):
    jd_id: Optional[str] = None
    company: Optional[str] = None
    city: Optional[str] = None
    job_type: Optional[str] = None
    seniority: Optional[str] = None
    sector: Optional[str] = None
    hard_requirements: List[str] = Field(default_factory=list)
    soft_requirements: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    pitch_probability: Optional[float] = None
    model_test_probability: Optional[float] = None
    source_url: Optional[str] = None
    collected_date: Optional[str] = None
