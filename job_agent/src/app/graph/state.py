from typing import List, TypedDict


class InvestmentJobState(TypedDict, total=False):
    # ── inputs ───────────────────────────────────────────────────────────────────
    resume_text: str          # raw resume text (pasted or extracted)
    jd_text: str              # raw job description text
    target_city: str          # optional override: "Hong Kong" | "Shanghai"
    target_sector: str        # optional override: "healthcare" | "tmt" | etc.

    # ── agent outputs ────────────────────────────────────────────────────────────
    jd_profile: dict          # structured JD fields from jd_parser_agent
    rag_query: str            # query string used for vector retrieval (for tracing)
    rag_cases: List[dict]     # top-k similar cases from rag_agent
    diagnosis: dict           # match_score, strengths, gaps, recommendation_priority
    resume_versions: dict     # sell_side_cn / buy_side_bilingual / hk_asset_mgmt_en
    interview_questions: List[str]  # 10 questions from interview_agent
    mock_answers: List[str]   # optional: user-provided or LLM-generated sample answers
    scores: dict              # optional: per-answer evaluation scores
    networking_drafts: dict   # referral_email_cn / linkedin_dm_en / thank_you_en
    final_report: str         # full Markdown report from final_report_agent
