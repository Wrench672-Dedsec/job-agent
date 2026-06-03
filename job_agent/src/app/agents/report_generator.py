"""Report Generator Agent

Assembles the ``final_report`` Markdown string from all upstream pipeline
outputs.  Sections rendered:

1. 岗位诊断总览    (jd_profile + diagnosis)
2. 简历版本建议    (resume_versions)
3. Cover Letter   (cover_letters)
4. 面试路线图      (interview_map)
5. 题库摘要        (question_bank)
6. Coaching 计划  (coaching_flow)
7. 外联 Networking(networking_drafts)  ← 本次完善重点
8. RAG 参考案例   (rag_cases)

All sections degrade gracefully when upstream data is missing.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.graph.state import InvestmentJobState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DIVIDER = "\n\n---\n\n"
_TEMPLATE_LABELS: Dict[str, str] = {
    "referral_email_cn":    "📧 中文内推冷邮件",
    "linkedin_dm_en":       "💼 LinkedIn 英文连接请求",
    "linkedin_followup_en": "🔁 LinkedIn 英文 7天跟进",
    "thank_you_en":         "🙏 英文面试感谢信",
    "info_interview_cn":    "☕ 中文 Informational Interview 申请",
    "offer_negotiation_cn": "🤝 中文 Offer 时间协商",
}


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}"


def _safe_list(val: Any) -> List:
    return val if isinstance(val, list) else []


def _safe_dict(val: Any) -> Dict:
    return val if isinstance(val, dict) else {}


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _section_diagnosis(jd_profile: dict, diagnosis: dict) -> str:
    lines = [_h(2, "一、岗位诊断总览")]
    firm    = jd_profile.get("firm_name", "—")
    role    = jd_profile.get("job_type", "—")
    city    = jd_profile.get("city", "—")
    sector  = jd_profile.get("sector", "—")
    score   = diagnosis.get("match_score", "—")
    summary = diagnosis.get("summary", "")
    strengths = _safe_list(diagnosis.get("strengths"))
    gaps      = _safe_list(diagnosis.get("gaps"))
    priority  = diagnosis.get("recommendation_priority", "")

    lines += [
        f"| 字段 | 内容 |",
        f"|------|------|",
        f"| 目标机构 | {firm} |",
        f"| 岗位类型 | {role} |",
        f"| 城市 | {city} |",
        f"| 行业 | {sector} |",
        f"| 匹配分 | **{score}** |",
    ]
    if summary:
        lines += ["", f"> {summary}"]
    if strengths:
        lines += ["", "**核心优势**"] + [f"- {s}" for s in strengths]
    if gaps:
        lines += ["", "**主要短板**"] + [f"- {g}" for g in gaps]
    if priority:
        lines += ["", f"**首要改进方向**：{priority}"]
    return "\n".join(lines)


def _section_resume(resume_versions: dict) -> str:
    if not resume_versions:
        return ""
    lines = [_h(2, "二、简历版本建议")]
    for version_key, content in resume_versions.items():
        label = version_key.replace("_", " ").title()
        lines.append(_h(3, label))
        if isinstance(content, str):
            lines.append(content)
        elif isinstance(content, dict):
            for k, v in content.items():
                lines.append(f"**{k}**: {v}")
    return "\n".join(lines)


def _section_cover_letters(cover_letters: list) -> str:
    if not cover_letters:
        return ""
    lines = [_h(2, "三、Cover Letter")]
    for i, cl in enumerate(cover_letters, 1):
        if isinstance(cl, dict):
            title = cl.get("title", f"版本 {i}")
            body  = cl.get("body", str(cl))
            lines += [_h(3, title), body]
        else:
            lines += [_h(3, f"版本 {i}"), str(cl)]
    return "\n".join(lines)


def _section_interview_map(interview_map: dict) -> str:
    if not interview_map:
        return ""
    lines = [_h(2, "四、面试路线图")]
    overview = interview_map.get("overview", "")
    rounds   = _safe_list(interview_map.get("rounds"))
    if overview:
        lines.append(f"> {overview}")
    for rnd in rounds:
        label = rnd.get("label", "Round")
        desc  = rnd.get("description", "")
        tips  = _safe_list(rnd.get("tips"))
        lines.append(_h(3, label))
        if desc:
            lines.append(desc)
        if tips:
            lines += [f"- {t}" for t in tips]
    return "\n".join(lines)


def _section_question_bank(question_bank: dict) -> str:
    if not question_bank:
        return ""
    lines = [_h(2, "五、面试题库摘要")]
    for category, questions in question_bank.items():
        lines.append(_h(3, category.replace("_", " ").title()))
        for q in _safe_list(questions):
            if isinstance(q, dict):
                lines.append(f"- **{q.get('question', '')}**")
                if q.get("answer_hint"):
                    lines.append(f"  > {q['answer_hint']}")
            else:
                lines.append(f"- {q}")
    return "\n".join(lines)


def _section_coaching(coaching_flow: dict) -> str:
    if not coaching_flow:
        return ""
    lines = [_h(2, "六、Coaching 行动计划")]
    summary    = coaching_flow.get("summary", "")
    weekly     = _safe_dict(coaching_flow.get("weekly_plan"))
    milestones = _safe_list(weekly.get("key_milestones"))
    weeks      = _safe_list(weekly.get("weeks"))

    if summary:
        lines.append(f"> {summary}")
    if milestones:
        lines += ["", "**关键里程碑**"] + [f"- {m}" for m in milestones]
    for wk in weeks:
        wnum  = wk.get("week", "")
        focus = wk.get("focus", "")
        tasks = _safe_list(wk.get("tasks"))
        lines.append(_h(3, f"第 {wnum} 周 — {focus}"))
        lines += [f"- {t}" for t in tasks]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Networking section (main improvement target)
# ---------------------------------------------------------------------------

def _render_template_block(key: str, tpl: dict) -> str:
    """Render a single networking template as a Markdown block."""
    label      = _TEMPLATE_LABELS.get(key, key)
    body       = tpl.get("body", "")
    tone       = tpl.get("tone", "")
    word_count = tpl.get("word_count", "")
    send_time  = tpl.get("send_timing", "")
    tips       = _safe_list(tpl.get("tips"))

    lines = [
        _h(3, label),
        f"> **发送时机**：{send_time}　｜　**语气**：{tone}　｜　**字数**：约 {word_count} 字",
        "",
        "```",
        body,
        "```",
    ]
    if tips:
        lines += ["", "**使用提示**"] + [f"- {t}" for t in tips]
    return "\n".join(lines)


def _section_networking(networking_drafts: dict) -> str:
    if not networking_drafts:
        return ""

    lines = [_h(2, "七、外联 & Networking 模板")]

    # --- Outreach strategy narrative ---
    strategy = networking_drafts.get("outreach_strategy", "")
    if strategy:
        lines += ["", _h(3, "外联策略建议"), strategy]

    # --- Target contacts table ---
    contacts: List[dict] = _safe_list(networking_drafts.get("target_contacts"))
    if contacts:
        lines += [
            "",
            _h(3, "目标联系人优先级"),
            "| 优先级 | 联系人类型 | 渠道 | 目标 | 备注 |",
            "|--------|-----------|------|------|------|",
        ]
        for c in contacts:
            rank  = c.get("rank", "")
            ctype = c.get("contact_type", "")
            chan  = c.get("channel", "")
            goal  = c.get("goal", "")
            note  = c.get("note", "")
            lines.append(f"| {rank} | {ctype} | {chan} | {goal} | {note} |")

    # --- 6 templates ---
    templates: dict = _safe_dict(networking_drafts.get("templates"))
    if templates:
        lines += ["", _h(3, "沟通模板库（6 份）"), ""]
        template_order = [
            "referral_email_cn",
            "linkedin_dm_en",
            "linkedin_followup_en",
            "thank_you_en",
            "info_interview_cn",
            "offer_negotiation_cn",
        ]
        for key in template_order:
            tpl = templates.get(key)
            if tpl:
                lines += ["", _render_template_block(key, tpl)]

    meta = _safe_dict(networking_drafts.get("meta"))
    if meta:
        count = meta.get("template_count", len(templates))
        lines += ["", f"*共 {count} 份模板 · 岗位类型：{meta.get('job_type','—')} · 城市：{meta.get('city','—')} · 行业：{meta.get('sector','—')}*"]

    return "\n".join(lines)


def _section_rag(rag_cases: list) -> str:
    if not rag_cases:
        return ""
    lines = [_h(2, "八、RAG 参考案例")]
    for i, case in enumerate(rag_cases[:5], 1):  # cap at 5
        if isinstance(case, dict):
            title   = case.get("title", f"案例 {i}")
            snippet = case.get("snippet", case.get("content", ""))
            source  = case.get("source", "")
            lines.append(_h(3, f"{i}. {title}"))
            if snippet:
                lines.append(snippet[:400] + ("…" if len(snippet) > 400 else ""))
            if source:
                lines.append(f"*来源：{source}*")
        else:
            lines.append(f"- {case}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public agent (graph node)
# ---------------------------------------------------------------------------

def report_generator_agent(state: InvestmentJobState) -> Dict[str, str]:
    jd_profile       = _safe_dict(state.get("jd_profile"))
    diagnosis        = _safe_dict(state.get("diagnosis"))
    resume_versions  = _safe_dict(state.get("resume_versions"))
    cover_letters    = _safe_list(state.get("cover_letters"))
    interview_map    = _safe_dict(state.get("interview_map"))
    question_bank    = _safe_dict(state.get("question_bank"))
    coaching_flow    = _safe_dict(state.get("coaching_flow"))
    networking_drafts= _safe_dict(state.get("networking_drafts"))
    rag_cases        = _safe_list(state.get("rag_cases"))

    firm = jd_profile.get("firm_name", "目标机构")
    role = jd_profile.get("job_type",  "岗位")

    header = "\n".join([
        _h(1, f"求职分析报告 — {firm} · {role}"),
        "",
        "> 由 Job Agent 自动生成，请结合实际情况调整。",
    ])

    sections = [
        header,
        _section_diagnosis(jd_profile, diagnosis),
        _section_resume(resume_versions),
        _section_cover_letters(cover_letters),
        _section_interview_map(interview_map),
        _section_question_bank(question_bank),
        _section_coaching(coaching_flow),
        _section_networking(networking_drafts),
        _section_rag(rag_cases),
    ]

    final_report = _DIVIDER.join(s for s in sections if s)

    logger.info(
        "report_generator: assembled report (%d chars) for %s / %s.",
        len(final_report), firm, role,
    )
    return {"final_report": final_report}
