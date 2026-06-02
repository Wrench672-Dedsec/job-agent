from typing import Dict

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def networking_agent(state: InvestmentJobState) -> Dict[str, dict]:
    drafts = {
        "referral_email_cn": "Hello [Name], I am applying for [Role] and would value your advice on the team. If it is not convenient, I completely understand.",
        "linkedin_dm_en": "Hi [Name], I saw your work in equity research and would appreciate a short chat to learn about your team.",
        "thank_you_en": "Thank you for the interview today. I appreciated the discussion on [topic] and would be excited to contribute.",
    }
    prompt = "Write referral_email_cn, linkedin_dm_en, and thank_you_en drafts for a job search assistant. Return JSON only."
    drafts = generate_json(prompt, drafts)
    return {"networking_drafts": drafts}
