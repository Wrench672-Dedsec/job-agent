from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models for structured fields
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# InterviewMap sub-models
# ---------------------------------------------------------------------------

class InterviewRound(BaseModel):
    """One round in the interview map (e.g. HR screen, PM, Partner)."""
    round: int
    label: str
    focus: Optional[str] = None
    modules: List[str] = Field(default_factory=list)
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    follow_ups: List[str] = Field(default_factory=list)


class MockPlan(BaseModel):
    total_questions: int = 0
    estimated_minutes: int = 0
    round_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    session_order: List[str] = Field(default_factory=list)


class InterviewMap(BaseModel):
    """Output of the interview_map agent."""
    job_type: Optional[str] = None
    city: Optional[str] = None
    sector: Optional[str] = None
    rounds: List[InterviewRound] = Field(default_factory=list)
    mock_plan: MockPlan = Field(default_factory=MockPlan)
    coaching_tips: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# CoachingFlow sub-models
# ---------------------------------------------------------------------------

class CoachingPhase(BaseModel):
    """One phase in the coaching flow (e.g. internship recall, stock pitch)."""
    phase_id: int
    phase_name: str
    status: str = "pending"          # pending | active | done
    source: str                       # e.g. "coaching_session.internship_drills"
    description: Optional[str] = None
    llm_intro: Optional[str] = None
    items: List[Any] = Field(default_factory=list)
    item_count: int = 0


class OverallProgress(BaseModel):
    total_phases: int = 4
    completed: int = 0
    pct: int = 0


class WeeklyPlanDay(BaseModel):
    day: int
    theme: str
    tasks: List[str] = Field(default_factory=list)
    duration_min: int = 120
    milestone: Optional[str] = None


class WeeklyPlan(BaseModel):
    days: List[WeeklyPlanDay] = Field(default_factory=list)
    total_hours: float = 0.0
    key_milestones: List[str] = Field(default_factory=list)


class CoachingFlowMeta(BaseModel):
    job_type: Optional[str] = None
    sector: Optional[str] = None
    total_items: int = 0


class CoachingFlow(BaseModel):
    """Output of the coaching_flow agent."""
    phases: List[CoachingPhase] = Field(default_factory=list)
    overall_progress: OverallProgress = Field(default_factory=OverallProgress)
    next_action: Optional[str] = None
    coaching_tips: List[str] = Field(default_factory=list)
    weekly_plan: WeeklyPlan = Field(default_factory=WeeklyPlan)
    meta: CoachingFlowMeta = Field(default_factory=CoachingFlowMeta)


# ---------------------------------------------------------------------------
# API request / response
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    resume_text: str
    jd_text: str
    target_city: Optional[str] = None
    target_sector: Optional[str] = None
    jd_url: Optional[str] = None          # single JD URL (alternative to jd_text)
    jd_urls: List[str] = Field(default_factory=list)  # batch JD URLs
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class RunResponse(BaseModel):
    # Core outputs (always present)
    jd_profile: Dict[str, Any] = Field(default_factory=dict)
    diagnosis: Dict[str, Any] = Field(default_factory=dict)
    resume_versions: Dict[str, Any] = Field(default_factory=dict)
    final_report: str = ""

    # Interview pipeline
    question_bank: Dict[str, Any] = Field(
        default_factory=dict,
        description="Full question bank: technical / behavioral / stock_pitch_drills / meta",
    )
    interview_map: InterviewMap = Field(
        default_factory=InterviewMap,
        description="Round-by-round interview map with mock plan and coaching tips",
    )
    interview_questions: List[str] = Field(
        default_factory=list,
        description="Legacy flat list of interview questions (kept for backwards compat)",
    )

    # Coaching pipeline
    coaching_session: Dict[str, Any] = Field(
        default_factory=dict,
        description="Internship recall drills + stock pitch scaffold from resume_coach",
    )
    coaching_flow: CoachingFlow = Field(
        default_factory=CoachingFlow,
        description="Phase-gated coaching plan merging coaching_session + interview_map",
    )

    # Supporting outputs
    cover_letters: List[Dict[str, Any]] = Field(default_factory=list)
    networking_drafts: Dict[str, Any] = Field(default_factory=dict)
    rag_cases: List[Dict[str, Any]] = Field(default_factory=list)
    collected_jds: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="JDs collected by jd_scraper (populated when jd_urls provided)",
    )
