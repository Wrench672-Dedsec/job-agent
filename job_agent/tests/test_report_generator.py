"""Unit tests for app.agents.report_generator.

All tests are pure-Python, no LLM calls, no network access.
Covers:
  - Individual section renderers (_section_*)
  - Networking section in full detail (strategy / contacts table / 6 templates)
  - report_generator_agent() end-to-end with a full mock state
  - Graceful degradation when upstream data is missing
  - Output always contains mandatory Markdown structure
"""
from __future__ import annotations

import pytest

from app.agents.report_generator import (
    report_generator_agent,
    _section_diagnosis,
    _section_resume,
    _section_cover_letters,
    _section_interview_map,
    _section_question_bank,
    _section_coaching,
    _section_networking,
    _section_rag,
    _render_template_block,
    _TEMPLATE_LABELS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def jd_profile() -> dict:
    return {
        "firm_name": "Greenwoods Asset Management",
        "job_type": "equity research analyst",
        "city": "Hong Kong",
        "sector": "TMT",
    }


@pytest.fixture()
def diagnosis() -> dict:
    return {
        "match_score": "72/100",
        "summary": "Strong quant background, limited sell-side writing samples.",
        "strengths": ["Python modelling", "Healthcare policy research"],
        "gaps": ["No published research note", "Limited financial modelling"],
        "recommendation_priority": "Produce one sector note on TMT within 2 weeks",
    }


@pytest.fixture()
def resume_versions() -> dict:
    return {
        "buy_side_hk": "Tailored for HK buy-side: emphasis on quant & sector coverage.",
        "sell_side_sh": "Tailored for SH sell-side: emphasis on macro & report writing.",
    }


@pytest.fixture()
def cover_letters() -> list:
    return [
        {"title": "Greenwoods HK Cover Letter", "body": "Dear Hiring Manager, ..."},
        {"title": "Fidelity HK Cover Letter",   "body": "To the Investment Team, ..."},
    ]


@pytest.fixture()
def interview_map() -> dict:
    return {
        "overview": "3-round process: HR screen, technical, partner fit.",
        "rounds": [
            {"label": "Round 1 — HR Screen",    "description": "30-min behavioural.", "tips": ["Prepare STAR stories"]},
            {"label": "Round 2 — Technical",     "description": "Stock pitch + modelling.", "tips": ["Prepare 1 long + 1 short"]},
            {"label": "Round 3 — Partner Fit",  "description": "Culture & motivation.", "tips": ["Research PM background"]},
        ],
        "mock_plan": {"total_questions": 20, "estimated_minutes": 90, "session_order": ["HR", "Technical", "Fit"]},
        "coaching_tips": "Focus on concise pitch delivery.",
    }


@pytest.fixture()
def question_bank() -> dict:
    return {
        "technical": [
            {"question": "Walk me through a DCF.", "answer_hint": "FCFF/FCFE, WACC, terminal value."},
        ],
        "behavioural": [
            {"question": "Tell me about a time you changed your view."},
        ],
    }


@pytest.fixture()
def coaching_flow() -> dict:
    return {
        "summary": "4-phase plan over 6 weeks targeting HK buy-side.",
        "overall_progress": {"completed": 1, "total_phases": 4, "pct": 25},
        "next_action": "Draft TMT sector note by Friday",
        "weekly_plan": {
            "key_milestones": ["Sector note drafted", "3 mock interviews done"],
            "weeks": [
                {"week": 1, "focus": "Sector note", "tasks": ["Pick 3 TMT names", "Build comp table"]},
                {"week": 2, "focus": "Mock interviews", "tasks": ["Pitch rehearsal x2", "Technical Q&A"]},
            ],
        },
    }


@pytest.fixture()
def networking_drafts() -> dict:
    tpl = {
        "body": "[NAME] 您好，我是 [YOUR_NAME]。",
        "tone": "formal",
        "word_count": 120,
        "send_timing": "投递后 48 小时内",
        "tips": ["主题行写清岗位", "避免套话"],
    }
    return {
        "outreach_strategy": "优先联系在职分析师，其次是师兄师姐。",
        "target_contacts": [
            {"rank": 1, "contact_type": "HK buy-side 分析师", "channel": "LinkedIn", "goal": "informational interview", "note": "2-5年经验优先"},
            {"rank": 2, "contact_type": "TMT 师兄师姐",       "channel": "微信",      "goal": "内推",                  "note": "提前准备 sector note"},
        ],
        "templates": {
            "referral_email_cn":    tpl,
            "linkedin_dm_en":       tpl,
            "linkedin_followup_en": tpl,
            "thank_you_en":         tpl,
            "info_interview_cn":    tpl,
            "offer_negotiation_cn": tpl,
        },
        "meta": {"template_count": 6, "job_type": "equity research analyst", "city": "Hong Kong", "sector": "TMT"},
    }


@pytest.fixture()
def rag_cases() -> list:
    return [
        {"title": "港中大金融转投研案例", "snippet": "该候选人利用行业研究补强实习经验。", "source": "公众号 A"},
        {"title": "TMT 覆盖报告写作案例",     "snippet": "首份 sector note 帮助获得面试机会。",  "source": "公众号 B"},
    ]


@pytest.fixture()
def full_state(
    jd_profile, diagnosis, resume_versions, cover_letters,
    interview_map, question_bank, coaching_flow, networking_drafts, rag_cases,
) -> dict:
    return {
        "jd_profile":        jd_profile,
        "diagnosis":         diagnosis,
        "resume_versions":   resume_versions,
        "cover_letters":     cover_letters,
        "interview_map":     interview_map,
        "question_bank":     question_bank,
        "coaching_flow":     coaching_flow,
        "networking_drafts": networking_drafts,
        "rag_cases":         rag_cases,
        # other state keys that report_generator ignores
        "interview_questions": [],
        "coaching_session":    {},
        "collected_jds":       [],
    }


# ---------------------------------------------------------------------------
# _section_diagnosis
# ---------------------------------------------------------------------------

class TestSectionDiagnosis:
    def test_contains_firm_and_role(self, jd_profile, diagnosis):
        out = _section_diagnosis(jd_profile, diagnosis)
        assert "Greenwoods Asset Management" in out
        assert "equity research analyst" in out

    def test_contains_match_score(self, jd_profile, diagnosis):
        out = _section_diagnosis(jd_profile, diagnosis)
        assert "72/100" in out

    def test_contains_strengths_and_gaps(self, jd_profile, diagnosis):
        out = _section_diagnosis(jd_profile, diagnosis)
        assert "Python modelling" in out
        assert "No published research note" in out

    def test_contains_priority(self, jd_profile, diagnosis):
        out = _section_diagnosis(jd_profile, diagnosis)
        assert "首要改进方向" in out

    def test_empty_diagnosis_returns_table(self, jd_profile):
        out = _section_diagnosis(jd_profile, {})
        assert "岗位诊断总览" in out
        assert "—" in out  # fallback dashes


# ---------------------------------------------------------------------------
# _section_resume
# ---------------------------------------------------------------------------

class TestSectionResume:
    def test_contains_version_keys(self, resume_versions):
        out = _section_resume(resume_versions)
        assert "Buy Side Hk" in out or "buy_side_hk" in out.lower()
        assert "Sell Side Sh" in out or "sell_side_sh" in out.lower()

    def test_empty_returns_empty_string(self):
        assert _section_resume({}) == ""

    def test_dict_value_rendered(self, resume_versions):
        out = _section_resume(resume_versions)
        assert "quant" in out


# ---------------------------------------------------------------------------
# _section_cover_letters
# ---------------------------------------------------------------------------

class TestSectionCoverLetters:
    def test_contains_titles(self, cover_letters):
        out = _section_cover_letters(cover_letters)
        assert "Greenwoods HK Cover Letter" in out
        assert "Fidelity HK Cover Letter" in out

    def test_contains_body(self, cover_letters):
        out = _section_cover_letters(cover_letters)
        assert "Dear Hiring Manager" in out

    def test_empty_list_returns_empty(self):
        assert _section_cover_letters([]) == ""

    def test_plain_string_items(self):
        out = _section_cover_letters(["Plain text cover letter."])
        assert "Plain text cover letter." in out


# ---------------------------------------------------------------------------
# _section_interview_map
# ---------------------------------------------------------------------------

class TestSectionInterviewMap:
    def test_contains_round_labels(self, interview_map):
        out = _section_interview_map(interview_map)
        assert "HR Screen" in out
        assert "Technical" in out
        assert "Partner Fit" in out

    def test_contains_overview(self, interview_map):
        out = _section_interview_map(interview_map)
        assert "3-round process" in out

    def test_contains_tips(self, interview_map):
        out = _section_interview_map(interview_map)
        assert "STAR stories" in out

    def test_empty_returns_empty(self):
        assert _section_interview_map({}) == ""


# ---------------------------------------------------------------------------
# _section_question_bank
# ---------------------------------------------------------------------------

class TestSectionQuestionBank:
    def test_contains_questions(self, question_bank):
        out = _section_question_bank(question_bank)
        assert "Walk me through a DCF" in out
        assert "Tell me about a time" in out

    def test_contains_answer_hint(self, question_bank):
        out = _section_question_bank(question_bank)
        assert "WACC" in out

    def test_empty_returns_empty(self):
        assert _section_question_bank({}) == ""


# ---------------------------------------------------------------------------
# _section_coaching
# ---------------------------------------------------------------------------

class TestSectionCoaching:
    def test_contains_summary(self, coaching_flow):
        out = _section_coaching(coaching_flow)
        assert "4-phase plan" in out

    def test_contains_milestones(self, coaching_flow):
        out = _section_coaching(coaching_flow)
        assert "Sector note drafted" in out

    def test_contains_weekly_focus(self, coaching_flow):
        out = _section_coaching(coaching_flow)
        assert "Sector note" in out
        assert "Mock interviews" in out

    def test_contains_tasks(self, coaching_flow):
        out = _section_coaching(coaching_flow)
        assert "Pick 3 TMT names" in out

    def test_empty_returns_empty(self):
        assert _section_coaching({}) == ""


# ---------------------------------------------------------------------------
# _render_template_block
# ---------------------------------------------------------------------------

class TestRenderTemplateBlock:
    @pytest.fixture()
    def sample_tpl(self):
        return {
            "body": "[NAME] 您好，我是 [YOUR_NAME]。",
            "tone": "formal",
            "word_count": 120,
            "send_timing": "投递后 48 小时内",
            "tips": ["主题行写清岗位", "避免套话"],
        }

    def test_body_in_code_block(self, sample_tpl):
        out = _render_template_block("referral_email_cn", sample_tpl)
        assert "```" in out
        assert "[NAME]" in out

    def test_label_rendered(self, sample_tpl):
        out = _render_template_block("referral_email_cn", sample_tpl)
        assert _TEMPLATE_LABELS["referral_email_cn"] in out

    def test_send_timing_rendered(self, sample_tpl):
        out = _render_template_block("referral_email_cn", sample_tpl)
        assert "投递后 48 小时内" in out

    def test_tips_rendered(self, sample_tpl):
        out = _render_template_block("referral_email_cn", sample_tpl)
        assert "主题行写清岗位" in out

    def test_unknown_key_uses_key_as_label(self, sample_tpl):
        out = _render_template_block("custom_template", sample_tpl)
        assert "custom_template" in out


# ---------------------------------------------------------------------------
# _section_networking — detailed
# ---------------------------------------------------------------------------

class TestSectionNetworking:
    def test_section_header_present(self, networking_drafts):
        out = _section_networking(networking_drafts)
        assert "外联" in out
        assert "Networking" in out

    def test_outreach_strategy_present(self, networking_drafts):
        out = _section_networking(networking_drafts)
        assert "外联策略建议" in out
        assert "在职分析师" in out

    def test_contacts_table_rendered(self, networking_drafts):
        out = _section_networking(networking_drafts)
        assert "目标联系人优先级" in out
        assert "HK buy-side" in out
        assert "TMT 师兄师姐" in out

    def test_contacts_table_has_markdown_pipe(self, networking_drafts):
        out = _section_networking(networking_drafts)
        table_lines = [l for l in out.splitlines() if l.startswith("|")]
        assert len(table_lines) >= 3  # header + separator + at least 2 rows

    def test_all_six_template_labels_present(self, networking_drafts):
        out = _section_networking(networking_drafts)
        for label in _TEMPLATE_LABELS.values():
            assert label in out, f"Missing template label: {label}"

    def test_all_six_template_bodies_in_code_block(self, networking_drafts):
        out = _section_networking(networking_drafts)
        # each template wraps body in ``` ... ``` — 6 templates → 12 fences
        assert out.count("```") >= 12

    def test_meta_footer_present(self, networking_drafts):
        out = _section_networking(networking_drafts)
        assert "TMT" in out
        assert "Hong Kong" in out

    def test_empty_returns_empty(self):
        assert _section_networking({}) == ""

    def test_missing_strategy_skips_gracefully(self, networking_drafts):
        nd = {**networking_drafts, "outreach_strategy": ""}
        out = _section_networking(nd)
        assert "外联策略建议" not in out
        assert "目标联系人优先级" in out  # rest still renders

    def test_missing_templates_skips_gracefully(self, networking_drafts):
        nd = {**networking_drafts, "templates": {}}
        out = _section_networking(nd)
        assert "外联" in out  # section still renders
        assert "```" not in out  # no template code blocks

    def test_partial_templates_renders_available(self, networking_drafts):
        nd = dict(networking_drafts)
        nd["templates"] = {"referral_email_cn": networking_drafts["templates"]["referral_email_cn"]}
        out = _section_networking(nd)
        assert _TEMPLATE_LABELS["referral_email_cn"] in out
        # other labels should NOT appear
        assert _TEMPLATE_LABELS["linkedin_dm_en"] not in out


# ---------------------------------------------------------------------------
# _section_rag
# ---------------------------------------------------------------------------

class TestSectionRag:
    def test_contains_case_titles(self, rag_cases):
        out = _section_rag(rag_cases)
        assert "港中大金融" in out
        assert "TMT" in out

    def test_contains_snippets(self, rag_cases):
        out = _section_rag(rag_cases)
        assert "行业研究" in out

    def test_contains_source(self, rag_cases):
        out = _section_rag(rag_cases)
        assert "公众号 A" in out

    def test_caps_at_five(self):
        cases = [{"title": f"案例 {i}", "snippet": f"content {i}"} for i in range(10)]
        out = _section_rag(cases)
        assert "案例 4" in out
        assert "案例 5" not in out  # 0-indexed: titles are 案例 0..案例 4

    def test_long_snippet_truncated(self):
        long_case = [{"title": "Long", "snippet": "x" * 600}]
        out = _section_rag(long_case)
        assert "…" in out

    def test_empty_returns_empty(self):
        assert _section_rag([]) == ""

    def test_plain_string_items(self):
        out = _section_rag(["简单案例文本"])
        assert "简单案例文本" in out


# ---------------------------------------------------------------------------
# report_generator_agent — end-to-end
# ---------------------------------------------------------------------------

class TestReportGeneratorAgent:
    def test_returns_final_report_key(self, full_state):
        result = report_generator_agent(full_state)
        assert "final_report" in result

    def test_report_is_string(self, full_state):
        result = report_generator_agent(full_state)
        assert isinstance(result["final_report"], str)

    def test_report_not_empty(self, full_state):
        result = report_generator_agent(full_state)
        assert len(result["final_report"]) > 200

    def test_report_starts_with_h1(self, full_state):
        result = report_generator_agent(full_state)
        assert result["final_report"].startswith("# ")

    def test_report_contains_firm_name(self, full_state):
        result = report_generator_agent(full_state)
        assert "Greenwoods Asset Management" in result["final_report"]

    def test_report_contains_all_section_headers(self, full_state):
        report = report_generator_agent(full_state)["final_report"]
        expected_headers = [
            "岗位诊断总览",
            "简历版本建议",
            "Cover Letter",
            "面试路线图",
            "题库摘要",
            "Coaching",
            "外联",
            "RAG",
        ]
        for header in expected_headers:
            assert header in report, f"Missing section: {header}"

    def test_report_networking_section_complete(self, full_state):
        report = report_generator_agent(full_state)["final_report"]
        # strategy
        assert "在职分析师" in report
        # contacts table
        assert "HK buy-side" in report
        # all 6 template labels
        for label in _TEMPLATE_LABELS.values():
            assert label in report, f"Missing networking template: {label}"

    def test_sections_separated_by_divider(self, full_state):
        report = report_generator_agent(full_state)["final_report"]
        assert "---" in report

    def test_empty_state_returns_minimal_report(self):
        result = report_generator_agent({})
        assert "final_report" in result
        assert isinstance(result["final_report"], str)
        # should at least have title
        assert "#" in result["final_report"]

    def test_missing_networking_skips_section(self, full_state):
        state = {**full_state, "networking_drafts": {}}
        report = report_generator_agent(state)["final_report"]
        # section should not appear
        for label in _TEMPLATE_LABELS.values():
            assert label not in report

    def test_missing_rag_skips_section(self, full_state):
        state = {**full_state, "rag_cases": []}
        report = report_generator_agent(state)["final_report"]
        assert "RAG" not in report

    def test_missing_cover_letters_skips_section(self, full_state):
        state = {**full_state, "cover_letters": []}
        report = report_generator_agent(state)["final_report"]
        assert "Cover Letter" not in report

    def test_report_contains_match_score(self, full_state):
        report = report_generator_agent(full_state)["final_report"]
        assert "72/100" in report

    def test_report_contains_coaching_milestone(self, full_state):
        report = report_generator_agent(full_state)["final_report"]
        assert "Sector note drafted" in report

    def test_report_contains_rag_case(self, full_state):
        report = report_generator_agent(full_state)["final_report"]
        assert "港中大金融" in report
