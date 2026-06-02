from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState


def _to_bullets(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ["Add 2-3 impact bullets with metrics", "Add a stock pitch example"]
    bullets = []
    for line in lines[:3]:
        trimmed = line[:120]
        bullets.append(trimmed)
    return bullets


def rewriter_agent(state: InvestmentJobState) -> Dict[str, dict]:
    resume_text = state.get("resume_text", "")
    bullets = _to_bullets(resume_text)

    versions = {
        "sell_side_cn": bullets,
        "buy_side_bilingual": bullets,
        "hk_asset_mgmt_en": bullets,
    }
    prompt = f"Rewrite the resume into three versions: sell_side_cn, buy_side_bilingual, hk_asset_mgmt_en. Resume text: {resume_text}. Return JSON only."
    versions = generate_json(prompt, versions)
    return {"resume_versions": versions}
