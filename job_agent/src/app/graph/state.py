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

    # ── interview_map outputs ─────────────────────────────────────────────────
    interview_map: Dict[str, Any]
    # {
    #   job_type, city, sector,
    #   rounds: [{round, label, modules, focus, questions, follow_ups}],
    #   mock_plan: {total_questions, estimated_minutes, round_breakdown, session_order},
    #   coaching_tips: str,
    # }

    # ── interview agent outputs (legacy flat list) ────────────────────────────
    interview_questions: List[str]
    mock_answers: List[str]
    scores: Dict[str, Any]

    # ── resume coach outputs ──────────────────────────────────────────────────
    coaching_session: Dict[str, Any]
    # {
    #   internship_drills: [{internship_index, excerpt, recall_questions}],
    #   pitch_scaffold: {pitch_template, drill_questions},
    #   usage_note: str,
    # }

    # ── coaching_flow outputs ─────────────────────────────────────────────────
    coaching_flow: Dict[str, Any]
    # {
    #   phases: [
    #     {
    #       phase_id: int,
    #       phase_name: str,
    #       status: "pending" | "active" | "done",
    #       source: str,
    #       description: str,
    #       llm_intro: str,
    #       items: [...],
    #       item_count: int,
    #     }
    #   ],
    #   overall_progress: {total_phases, completed, pct},
    #   next_action: str,
    #   coaching_tips: [str],
    #   weekly_plan: {days: [...], total_hours, key_milestones},
    #   meta: {job_type, sector, total_items},
    # }

    # ── networking outputs ────────────────────────────────────────────────────
    networking_drafts: Dict[str, Any]

    # ── final report ──────────────────────────────────────────────────────────
    final_report: str
