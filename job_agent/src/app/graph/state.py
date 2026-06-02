from typing import Any, Dict, List, TypedDict


class InvestmentJobState(TypedDict, total=False):
    # ── user inputs ───────────────────────────────────────────────────────────
    resume_text: str          # raw resume text (pasted or PDF-extracted)
    jd_text: str              # single JD text (manual paste)
    jd_urls: List[str]        # explicit list of JD URLs to fetch
    target_city: str          # "Hong Kong" | "Shanghai" | ...
    target_sector: str        # "healthcare" | "tmt" | "new energy" | "generalist"

    # ── jd_scraper outputs ─────────────────────────────────────────────────────
    collected_jds: List[Dict[str, Any]]  # [{title, company, city, source_url, raw_text}]

    # ── jd_parser outputs ─────────────────────────────────────────────────────
    jd_profile: Dict[str, Any]   # job_type/city/sector/hard_reqs/...

    # ── rag outputs ────────────────────────────────────────────────────────────
    rag_query: str               # query string used for vector retrieval
    rag_cases: List[Dict[str, Any]]  # top-k similar candidate cases

    # ── diagnosis outputs ──────────────────────────────────────────────────────
    diagnosis: Dict[str, Any]    # match_score/strengths/gaps/recommendation_priority

    # ── rewriter outputs ──────────────────────────────────────────────────────
    resume_versions: Dict[str, Any]  # sell_side_cn/buy_side_bilingual/hk_asset_mgmt_en

    # ── cover_letter outputs ──────────────────────────────────────────────────
    cover_letters: List[Dict[str, Any]]  # per-JD: cover_letter_cn/en + resume_patch

    # ── question bank outputs ───────────────────────────────────────────────
    question_bank: Dict[str, Any]  # technical/behavioral/stock_pitch_drills/meta

    # ── interview agent outputs (legacy: 10 Qs list) ───────────────────────
    interview_questions: List[str]  # quick-access flat list (subset of bank)
    mock_answers: List[str]         # user or LLM sample answers
    scores: Dict[str, Any]          # per-answer evaluation scores

    # ── resume coach outputs ──────────────────────────────────────────────────
    coaching_session: Dict[str, Any]  # internship_drills + pitch_scaffold

    # ── networking outputs ─────────────────────────────────────────────────────
    networking_drafts: Dict[str, Any]  # referral_email_cn/linkedin_dm_en/thank_you_en

    # ── final report ──────────────────���──────────────────────────────────────────
    final_report: str              # full Markdown report
