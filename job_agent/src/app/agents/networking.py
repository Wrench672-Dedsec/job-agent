"""Networking Drafter Agent

Generates six outbound communication templates that are contextually aware of
the full upstream pipeline: jd_profile, diagnosis, coaching_flow, and
interview_map.

Templates
---------
1. referral_email_cn       — Chinese internal-referral cold email
2. linkedin_dm_en          — English LinkedIn DM (connection request)
3. linkedin_followup_en    — English LinkedIn follow-up after no reply (7-day)
4. thank_you_en            — English post-interview thank-you note
5. info_interview_cn       — Chinese informational-interview request
6. offer_negotiation_cn    — Chinese offer negotiation / timeline ask

Each template ships with:
  - body        : the draft text (with [PLACEHOLDER] tokens)
  - tone        : formal | semi-formal | warm
  - word_count  : approximate
  - send_timing : when to send this template
  - tips        : 2-3 bullet coaching notes

Additionally the agent emits:
  - outreach_strategy : LLM-generated 3-step approach narrative
  - target_contacts   : suggested contact types ranked by ROI
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.llm import generate_json, generate_text
from app.graph.state import InvestmentJobState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _context_summary(jd_profile: dict, diagnosis: dict,
                     coaching_flow: dict, interview_map: dict) -> str:
    """Build a compact context string to inject into every LLM prompt."""
    job_type = jd_profile.get("job_type", "equity research")
    city     = jd_profile.get("city", "Hong Kong")
    sector   = jd_profile.get("sector", "generalist")
    firm     = jd_profile.get("firm_name", "[Target Firm]")
    score    = diagnosis.get("match_score", "n/a")
    strengths = diagnosis.get("strengths", [])
    gaps      = diagnosis.get("gaps", [])
    priority  = diagnosis.get("recommendation_priority", "")

    # Pull coaching milestones if available
    milestones: List[str] = []
    wp = (coaching_flow.get("weekly_plan") or {})
    milestones = wp.get("key_milestones", [])

    # Pull interview round labels
    rounds = [r.get("label", "") for r in (interview_map.get("rounds") or [])]

    return (
        f"岗位类型: {job_type} | 城市: {city} | 行业: {sector} | 目标机构: {firm}\n"
        f"匹配分: {score} | 优势: {strengths} | 短板: {gaps}\n"
        f"首要改进: {priority}\n"
        f"面试轮次: {rounds}\n"
        f"Coaching 里程碑: {milestones}"
    )


def _build_template_prompt(template_name: str, context: str,
                           extra_instruction: str = "") -> str:
    return f"""
你是一位投研求职顾问，擅长帮助候选人撰写高转化率的求职沟通稿件。

候选人背景：
{context}

任务：生成「{template_name}」模板。
{extra_instruction}

请返回 JSON，格式如下：
{{
  "body": "邮件/消息正文（用 [NAME]、[FIRM]、[ROLE]、[DATE] 等占位符）",
  "tone": "formal | semi-formal | warm",
  "word_count": int,
  "send_timing": "何时发送（例如：投递后 48 小时内）",
  "tips": ["2-3 条使用建议"]
}}
"""


# ---------------------------------------------------------------------------
# Individual template generators
# ---------------------------------------------------------------------------

def _referral_email_cn(context: str) -> dict:
    extra = (
        "语言：中文。长度 150-200 字。"
        "要求：说明候选人与岗位的具体契合点（引用上方背景），"
        "避免套话，结尾给对方一个明确的低门槛行动（如：方便的话能否给 15 分钟电话）。"
    )
    fallback = {
        "body": (
            "[NAME] 您好，\n\n我是 [YOUR_NAME]，目前在 [CURRENT_INSTITUTION] 攻读 [DEGREE]。"
            "得知贵司 [FIRM] 正在招募 [ROLE] 岗位，我对此非常感兴趣。"
            "我在 [RELEVANT_EXPERIENCE] 方面积累了一定经验，对 [SECTOR] 赛道有持续追踪。"
            "\n\n如您方便，能否给我 15 分钟电话，了解岗位的具体要求？非常感谢。"
            "\n\n[YOUR_NAME]"
        ),
        "tone": "formal",
        "word_count": 120,
        "send_timing": "投递简历后 24-48 小时内",
        "tips": [
            "主题行加上岗位名称和你的名字，提高打开率",
            "第一段在 2 句内说清楚你是谁、为什么写这封信",
            "避免'请多关照'等无实质意义的客套话",
        ],
    }
    prompt = _build_template_prompt("中文内推冷邮件", context, extra)
    return generate_json(prompt, fallback)


def _linkedin_dm_en(context: str) -> dict:
    extra = (
        "Language: English. Max 300 characters (LinkedIn connection request limit). "
        "Focus on ONE specific commonality or genuine reason for reaching out. "
        "Do NOT say 'I came across your profile' — be specific."
    )
    fallback = {
        "body": (
            "Hi [NAME], I noticed your work on [SPECIFIC_TOPIC/DEAL/REPORT] at [FIRM]. "
            "I'm a [ROLE] candidate focused on [SECTOR] and would love a quick chat "
            "— completely understand if timing doesn't work."
        ),
        "tone": "warm",
        "word_count": 45,
        "send_timing": "投递当天或发现内推机会后立即发送",
        "tips": [
            "引用对方具体的文章、报告或公开观点，说明你真的做了功课",
            "不要在第一条消息里要求 referral",
            "300 字符上限，直接切入重点",
        ],
    }
    prompt = _build_template_prompt("LinkedIn 英文连接请求", context, extra)
    return generate_json(prompt, fallback)


def _linkedin_followup_en(context: str) -> dict:
    extra = (
        "Language: English. This is a 7-day follow-up when no reply was received. "
        "Max 80 words. Acknowledge they're busy, add ONE new piece of value "
        "(e.g., a sector insight, a question), and make it easy to say no."
    )
    fallback = {
        "body": (
            "Hi [NAME], just following up on my note from last week. "
            "I recently read [SPECIFIC_REPORT/NEWS] on [SECTOR] and thought it was "
            "relevant to [FIRM]'s coverage. Happy to share my take if useful — "
            "and no worries if now isn't a good time."
        ),
        "tone": "warm",
        "word_count": 55,
        "send_timing": "首次消息发出后 7 天无回复时",
        "tips": [
            "带上一个真实的行业观点，显示你持续在追踪",
            "最后一句给对方退出的台阶",
            "跟进超过 2 次后建议换渠道（邮件/活动认识）",
        ],
    }
    prompt = _build_template_prompt("LinkedIn 英文 7 天跟进消息", context, extra)
    return generate_json(prompt, fallback)


def _thank_you_en(context: str, interview_map: dict) -> dict:
    rounds = interview_map.get("rounds") or []
    round_labels = ", ".join(r.get("label", "") for r in rounds) or "[ROUND]"
    extra = (
        f"Language: English. Post-interview thank-you note (within 24 hours). "
        f"Interview rounds in this process: {round_labels}. "
        "150-200 words. Must reference ONE specific topic discussed in the interview "
        "(use [SPECIFIC_TOPIC] placeholder), reaffirm fit, and end with a "
        "forward-looking sentence."
    )
    fallback = {
        "body": (
            "Dear [NAME],\n\n"
            "Thank you for taking the time to speak with me today about the [ROLE] "
            "position at [FIRM]. I particularly enjoyed our discussion on [SPECIFIC_TOPIC] "
            "— it reinforced my conviction that the team's approach aligns well with "
            "how I think about [SECTOR] investing.\n\n"
            "The conversation gave me a much clearer picture of the research process "
            "and the calibre of the team. I'm genuinely excited about the opportunity "
            "and look forward to the next steps.\n\n"
            "Best regards,\n[YOUR_NAME]"
        ),
        "tone": "formal",
        "word_count": 110,
        "send_timing": "面试结束后 12-24 小时内",
        "tips": [
            "引用面试中一个具体讨论点，证明你在认真听",
            "不要在感谢信里催问结果",
            "发给每一位面试官单独定制版本",
        ],
    }
    prompt = _build_template_prompt("英文面试后感谢信", context, extra)
    return generate_json(prompt, fallback)


def _info_interview_cn(context: str) -> dict:
    extra = (
        "语言：中文。这是一封向行业前辈申请 informational interview 的邮件。"
        "200 字以内，说明你的背景、为什么找这位前辈（要具体）、"
        "你想了解的 1-2 个具体问题，以及你对他们时间的尊重（可以视频或电话，15 分钟即可）。"
    )
    fallback = {
        "body": (
            "[NAME] 您好，\n\n"
            "我是 [YOUR_NAME]，目前在 [INSTITUTION] 读 [DEGREE]，专注 [SECTOR] 研究。"
            "拜读了您在 [SPECIFIC_CONTEXT] 的分享，深受启发。\n\n"
            "我正在准备进入 [JOB_TYPE] 领域，有 1-2 个具体问题想请教："
            "[QUESTION_1]；[QUESTION_2]。"
            "如您百忙中能给 15 分钟视频或电话，将非常感激。"
            "时间完全以您方便为准。\n\n"
            "感谢，\n[YOUR_NAME]"
        ),
        "tone": "semi-formal",
        "word_count": 130,
        "send_timing": "在投递目标机构前 2-4 周发出，建立关系",
        "tips": [
            "问题要具体，避免问'你是怎么进投研的'这类过于宽泛的问题",
            "提前 research 对方的公开发言或报告，在邮件中引用",
            "结束后 48 小时内发一封简短的感谢回复",
        ],
    }
    prompt = _build_template_prompt("中文 Informational Interview 申请邮件", context, extra)
    return generate_json(prompt, fallback)


def _offer_negotiation_cn(context: str) -> dict:
    extra = (
        "语言：中文。候选人收到 offer 或进入终面后，需要争取时间或确认条件。"
        "150 字以内，语气诚恳不强硬，表达对机会的珍视，"
        "同时合理提出需要 [X] 天考虑或询问某一条件（用占位符）。"
    )
    fallback = {
        "body": (
            "[HR_NAME] 您好，\n\n"
            "非常感谢贵司给予的 offer，我对加入 [FIRM] 的 [ROLE] 岗位深感荣幸。"
            "我对这个机会非常重视，希望能在 [DATE] 前给您正式回复，"
            "以便我能认真考量并做好入职准备。请问这个时间安排是否可行？"
            "\n\n再次感谢，期待与您进一步确认。\n\n[YOUR_NAME]"
        ),
        "tone": "formal",
        "word_count": 95,
        "send_timing": "收到书面 offer 后 24 小时内回复",
        "tips": [
            "先表达感谢和热情，再提出时间需求，顺序很重要",
            "争取时间是正常的，通常 3-5 个工作日是合理区间",
            "如果有其他 offer 在考虑，不需要主动说明，除非对方直接问",
        ],
    }
    prompt = _build_template_prompt("中文 Offer 时间协商邮件", context, extra)
    return generate_json(prompt, fallback)


def _outreach_strategy(context: str, job_type: str, city: str) -> str:
    prompt = (
        f"你是投研求职顾问。请为以下候选人生成一段 150 字以内的外联策略建议，"
        f"说明：(1) 优先联系哪类人（按 ROI 排序），"
        f"(2) 在正式投递前应该完成哪些关系建立动作，"
        f"(3) 一条具体的差异化建议（针对 {job_type} + {city} 市场）。\n\n"
        f"候选人背景：\n{context}"
    )
    fallback = (
        f"优先联系：(1) 目标机构的在职分析师/研究员（LinkedIn 或校友网络），"
        f"(2) 同赛道已入行的师兄师姐，(3) 猎头（{city} 本地 buy-side 专注型）。\n"
        f"投递前动作：informational interview × 2，参加 1 次行业论坛/路演建立面孔。\n"
        f"差异化：在 {city} 市场，{job_type} 岗位竞争激烈，"
        f"一份针对目标机构持仓/策略的定制 pitch note 比简历更能打开对话。"
    )
    try:
        return generate_text(prompt, fallback=fallback)
    except Exception:  # noqa: BLE001
        return fallback


def _target_contacts(job_type: str, city: str, sector: str) -> List[dict]:
    return [
        {
            "rank": 1,
            "contact_type": f"{city} {job_type} 在职分析师 / 研究员",
            "channel": "LinkedIn / 校友网络",
            "goal": "informational interview + referral",
            "note": "优先找 2-5 年经验、最近有公开发言的人",
        },
        {
            "rank": 2,
            "contact_type": f"{sector} 行业已入行师兄师姐",
            "channel": "微信 / 校友群",
            "goal": "内推 / 面试经验分享",
            "note": "提前送上你准备好的一页 sector note 作为破冰",
        },
        {
            "rank": 3,
            "contact_type": f"{city} 专注 buy-side 的猎头",
            "channel": "LinkedIn / 招聘平台",
            "goal": "市场信息 + 被动机会",
            "note": "先建立关系，不要一上来就问有没有 JD",
        },
        {
            "rank": 4,
            "contact_type": "行业论坛 / 路演参与者",
            "channel": "线下活动",
            "goal": "建立面孔、扩展人脉",
            "note": f"关注 {city} CFA Society、HKFA、行业协会活动",
        },
    ]


# ---------------------------------------------------------------------------
# Public agent (graph mode)
# ---------------------------------------------------------------------------

def networking_agent(state: InvestmentJobState) -> Dict[str, Any]:
    jd_profile    = state.get("jd_profile")    or {}
    diagnosis     = state.get("diagnosis")     or {}
    coaching_flow = state.get("coaching_flow") or {}
    interview_map = state.get("interview_map") or {}

    job_type = jd_profile.get("job_type", "equity research")
    city     = jd_profile.get("city",     "Hong Kong")
    sector   = jd_profile.get("sector",   "generalist")

    ctx = _context_summary(jd_profile, diagnosis, coaching_flow, interview_map)

    templates = {
        "referral_email_cn":    _referral_email_cn(ctx),
        "linkedin_dm_en":       _linkedin_dm_en(ctx),
        "linkedin_followup_en": _linkedin_followup_en(ctx),
        "thank_you_en":         _thank_you_en(ctx, interview_map),
        "info_interview_cn":    _info_interview_cn(ctx),
        "offer_negotiation_cn": _offer_negotiation_cn(ctx),
    }

    strategy = _outreach_strategy(ctx, job_type, city)
    contacts = _target_contacts(job_type, city, sector)

    networking_drafts = {
        "templates":         templates,
        "outreach_strategy": strategy,
        "target_contacts":   contacts,
        "meta": {
            "template_count": len(templates),
            "job_type":       job_type,
            "city":           city,
            "sector":         sector,
        },
    }

    logger.info(
        "networking_agent: %d templates generated for %s / %s.",
        len(templates), job_type, city,
    )
    return {"networking_drafts": networking_drafts}
