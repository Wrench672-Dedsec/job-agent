"""coaching_flow.py

Orchestrates the 6-agent coaching pipeline using the role_taxonomy.
Each agent reads from JobState and writes back its output slice.
Compatible with the existing LangGraph graph in graph.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Taxonomy loader
# ---------------------------------------------------------------------------

_TAXONOMY_PATH = Path(__file__).parent.parent.parent / "data" / "role_taxonomy.json"


def load_taxonomy() -> dict[str, Any]:
    """Load role_taxonomy.json from job_agent/data/."""
    if not _TAXONOMY_PATH.exists():
        return {"roles": []}
    with open(_TAXONOMY_PATH, encoding="utf-8") as f:
        return json.load(f)


def match_role(target_city: str, target_sector: str, taxonomy: dict | None = None) -> dict[str, Any] | None:
    """Return the best-matching role entry for city + sector.

    Scoring: sum of len(keyword) for each keyword that is a substring of
    sector_lower.  Longer phrase matches score higher, resolving ambiguity
    between roles that share short keywords (e.g. both buy/sell share
    \u8986\u76d6 but sellside also matches \u884c\u4e1a\u8986\u76d6, \u7eaa\u8981 etc.).

    Phase 1: highest-scoring city-matched role with score > 0.
    Phase 2: fallback to city-matched role with highest sector_depth when no
              keyword matches at all.
    """
    if taxonomy is None:
        taxonomy = load_taxonomy()

    city_lower = target_city.lower()
    sector_lower = target_sector.lower()
    depth_order = {"very_high": 4, "high": 3, "medium": 2, "low": 1}

    scored: list[tuple[int, dict]] = []
    for role in taxonomy.get("roles", []):
        city_match = any(city_lower in c.lower() for c in role.get("city", []))
        if not city_match:
            continue
        candidates = (
            role.get("benchmark_jd_keywords", [])
            + role.get("en_aliases", [])
            + [role["label"]]
        )
        score = sum(len(kw) for kw in candidates if kw.lower() in sector_lower)
        scored.append((score, role))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_role = scored[0]
    if best_score > 0:
        return best_role

    # Fallback: no keyword hit — return highest sector_depth role in city
    return sorted(
        [r for _, r in scored],
        key=lambda r: depth_order.get(r.get("sector_depth", "low"), 0),
        reverse=True,
    )[0]


# ---------------------------------------------------------------------------
# Coaching prompt builders (called by each agent node)
# ---------------------------------------------------------------------------

def build_jd_parse_prompt(jd_text: str, role: dict | None) -> str:
    role_ctx = ""
    if role:
        role_ctx = (
            f"Target role type: {role['label']}\n"
            f"Interview style: {role['interview_style']}\n"
            f"Pitch format: {role['pitch_format']}\n"
        )
    return (
        f"{role_ctx}"
        f"Parse the following JD. Extract:\n"
        f"1. Must-have hard skills\n"
        f"2. Soft skills\n"
        f"3. Implicit screening criteria (e.g. firm tier, school tier, language)\n"
        f"4. Red flags for rejections\n\n"
        f"JD:\n{jd_text}"
    )


def build_diagnosis_prompt(
    resume_text: str,
    jd_analysis: str,
    role: dict | None,
) -> str:
    weakness_hints = ""
    if role:
        ws = ", ".join(role.get("weakness_signals", []))
        weakness_hints = f"Common weakness signals for this role type: {ws}\n"
    return (
        f"{weakness_hints}"
        f"Compare resume vs JD analysis. Output:\n"
        f"- gap_score: integer 1-10 (10 = perfect match)\n"
        f"- top_gaps: list of up to 5 critical gaps\n"
        f"- strengths: list of up to 4 competitive strengths\n"
        f"- priority_fix: the single most impactful fix\n\n"
        f"Resume:\n{resume_text}\n\n"
        f"JD Analysis:\n{jd_analysis}"
    )


def build_resume_rewrite_prompt(
    resume_text: str,
    diagnosis: str,
    role: dict | None,
) -> str:
    sector_depth = (role or {}).get("sector_depth", "medium")
    return (
        f"Sector depth expected by employer: {sector_depth}\n"
        f"Rewrite the resume to close the top gaps identified in the diagnosis.\n"
        f"Rules:\n"
        f"- Every bullet must start with a strong action verb\n"
        f"- Quantify impact wherever possible\n"
        f"- Mirror JD keywords naturally (no keyword stuffing)\n"
        f"- Output 2 versions: (A) concise 1-page, (B) detailed 2-page\n\n"
        f"Original resume:\n{resume_text}\n\n"
        f"Diagnosis:\n{diagnosis}"
    )


def build_interview_prompt(
    jd_analysis: str,
    diagnosis: str,
    role: dict | None,
) -> str:
    style = (role or {}).get("interview_style", "general")
    pitch_fmt = (role or {}).get("pitch_format", "standard pitch")
    return (
        f"Interview style: {style}\n"
        f"Expected pitch format: {pitch_fmt}\n"
        f"Generate 10 interview questions calibrated to this role and candidate gaps.\n"
        f"Include:\n"
        f"- 3 technical/modeling questions\n"
        f"- 2 stock pitch questions (use pitch format above)\n"
        f"- 2 behavioral questions targeting the top gaps\n"
        f"- 2 market/macro questions relevant to target sector\n"
        f"- 1 fit/motivation question\n"
        f"For each question add a 1-sentence ideal answer hint.\n\n"
        f"JD Analysis:\n{jd_analysis}\n\n"
        f"Candidate Diagnosis:\n{diagnosis}"
    )


def build_networking_prompt(
    resume_text: str,
    jd_analysis: str,
    role: dict | None,
) -> str:
    firm_types = ", ".join((role or {}).get("firm_types", ["target firm"]))
    lang = (role or {}).get("language", "zh")
    lang_note = "Draft in Chinese." if lang == "zh" else "Draft in English."
    return (
        f"Target firm types: {firm_types}\n"
        f"{lang_note}\n"
        f"Write 3 networking outreach drafts:\n"
        f"(A) Cold LinkedIn DM to a research analyst (\u2264100 words)\n"
        f"(B) Referral request to a mutual contact (\u2264120 words)\n"
        f"(C) Follow-up after a coffee chat (\u226480 words)\n"
        f"Each draft must mention a specific insight from the JD analysis.\n\n"
        f"Resume snippet (background only):\n{resume_text[:600]}\n\n"
        f"JD Analysis:\n{jd_analysis}"
    )


def build_case_retrieval_prompt(
    diagnosis: str,
    role: dict | None,
) -> str:
    role_label = (role or {}).get("label", "target role")
    return (
        f"You are a career coach with a database of successful job-search cases.\n"
        f"Target role: {role_label}\n"
        f"Candidate diagnosis summary:\n{diagnosis}\n\n"
        f"Retrieve and describe 2-3 analogous successful cases. For each case:\n"
        f"- Candidate background (anonymized)\n"
        f"- Key gap they overcame\n"
        f"- Specific action taken (not generic advice)\n"
        f"- Timeline and outcome\n"
        f"If no real cases available, generate plausible illustrative cases clearly marked [Illustrative]."
    )


# ---------------------------------------------------------------------------
# Coaching flow entry point (for direct testing without LangGraph)
# ---------------------------------------------------------------------------

def run_coaching_flow(
    resume_text: str,
    jd_text: str,
    target_city: str = "Shanghai",
    target_sector: str = "healthcare",
    llm_fn=None,  # callable(prompt: str) -> str; defaults to echo mock
) -> dict[str, Any]:
    """Run the 6-agent coaching flow and return all outputs as a dict."""
    if llm_fn is None:
        def llm_fn(prompt: str) -> str:  # noqa: F811
            return f"[mock] {prompt[:120]}..."

    role = match_role(target_city, target_sector)

    jd_analysis = llm_fn(build_jd_parse_prompt(jd_text, role))
    diagnosis = llm_fn(build_diagnosis_prompt(resume_text, jd_analysis, role))
    resume_versions = llm_fn(build_resume_rewrite_prompt(resume_text, diagnosis, role))
    interview_questions = llm_fn(build_interview_prompt(jd_analysis, diagnosis, role))
    networking_drafts = llm_fn(build_networking_prompt(resume_text, jd_analysis, role))
    case_retrieval = llm_fn(build_case_retrieval_prompt(diagnosis, role))

    return {
        "matched_role": role,
        "jd_analysis": jd_analysis,
        "diagnosis": diagnosis,
        "resume_versions": resume_versions,
        "interview_questions": interview_questions,
        "networking_drafts": networking_drafts,
        "case_retrieval": case_retrieval,
    }
