from __future__ import annotations

from typing import Dict

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def networking_agent(state: InvestmentJobState) -> Dict[str, dict]:
    jd_profile = state.get("jd_profile", {})
    diagnosis = state.get("diagnosis", {})

    job_type = jd_profile.get("job_type", "equity research")
    city = jd_profile.get("city", "Hong Kong")
    sector = jd_profile.get("sector", "generalist")
    score = diagnosis.get("match_score", "n/a")
    priority = diagnosis.get("recommendation_priority", "")

    fallback = {
        "referral_email_cn": (
            f"您好，我目前正在申请{city}的{job_type}岗位（{sector}方向），"
            "仒慷尺热情悳情悳连络请教。"
            "如不方便完全理解，谢谢。"
        ),
        "linkedin_dm_en": (
            f"Hi [Name], I’m exploring {job_type} opportunities in {city} "
            f"covering {sector}. I’d love a 15-minute chat to learn about your "
            "experience — completely understand if timing doesn’t work."
        ),
        "thank_you_en": (
            "Thank you for the interview today. The discussion on [specific topic] "
            "gave me a clearer picture of the team’s approach to research. "
            "I’m excited about the opportunity and look forward to next steps."
        ),
    }

    prompt = (
        f"为一位求职中的候选人起草三份求职沟通稿件。"
        f"背景：岗位={job_type}，城市={city}，行业={sector}，"
        f"匹配度={score}，优先改进方向={priority}。"
        "请返回 JSON，包含以下字段："
        "referral_email_cn（中文内推邮件）、"
        "linkedin_dm_en（英文 LinkedIn 私信）、"
        "thank_you_en（英文面试后感谢信）。"
        "各模板用 [Name]、[specific topic] 等占位符代替具体信息。"
    )

    drafts = generate_json(prompt, fallback)
    return {"networking_drafts": drafts}
