from typing import Any, Dict, List, TypedDict


class InvestmentJobState(TypedDict, total=False):
    # ── user inputs ───────────────────────────────────────────────────────────
    resume_text: str          # raw resume text (pasted or PDF-extracted)
    jd_text: str              # single JD text (manual paste)
    jd_urls: List[str]        # explicit list of JD URLs to fetch
    target_city: str          # "Hong Kong" | "Shanghai" | ...
    target_sector: str        # "healthcare" | "tmt" | "new energy" | "generalist"

    # ── jd_scraper outputs ────────────────────────────────────────────────────
    collected_jds: List[Dict[str, Any]]  # [{title, company, city, source_url, raw_text}]

    # ── jd_parser outputs ─────────────────────────────────────────────────────
    jd_profile: Dict[str, Any]   # job_type/city/sector/hard_reqs/...

    # ── rag outputs ───────────────────────────────────────────────────────────
    rag_query: str
    rag_cases: List[Dict[str, Any]]

    # ── diagnosis outputs ─────────────────────────────────────────────────────
    diagnosis: Dict[str, Any]    # match_score/strengths/gaps/recommendation_priority

    # ── rewriter outputs ──────────────────────────────────────────────────────
    resume_versions: Dict[str, Any]

    # ── cover_letter outputs ──────────────────────────────────────────────────
    cover_letters: List[Dict[str, Any]]

    # ── question bank outputs ─────────────────────────────────────────────────
    question_bank: Dict[str, Any]  # technical/behavioral/stock_pitch_drills/meta

    # ── interview_map outputs (NEW) ───────────────────────────────────────────
    interview_map: Dict[str, Any]
    # {
    #   job_type: str,
    #   city: str,
    #   sector: str,
    #   rounds: [
    #     {
    #       round: int,
    #       label: str,
    #       modules: [str],
    #       focus: str,
    #       questions: [{q, type, eval}],
    #       follow_ups: [str],
    #     }
    #   ],
    #   mock_plan: {
    #     total_questions: int,
    #     estimated_minutes: int,
    #     round_breakdown: [...],
    #     session_order: [str],
    #   },
    #   coaching_tips: str,
    # }

    # ── interview agent outputs (legacy: 10 Qs flat list) ─────────────────────
    interview_questions: List[str]
    mock_answers: List[str]
    scores: Dict[str, Any]

    # ── resume coach outputs ──────────────────────────────────────────────────
    coaching_session: Dict[str, Any]

    # ── networking outputs ────────────────────────────────────────────────────
    networking_drafts: Dict[str, Any]

    # ── final report ──────────────────────────────────────────────────────────
    final_report: str
