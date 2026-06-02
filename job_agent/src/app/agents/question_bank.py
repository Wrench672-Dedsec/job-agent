from __future__ import annotations

"""Question Bank Agent

Builds a systematic interview question bank split into:
  - technical_questions: valuation / modelling / sector-specific / data/quant
  - behavioral_questions: STAR-format, role-specific
  - stock_pitch_drills: structured pitch practice prompts

Each question entry is a dict:
  { "id": str, "category": str, "difficulty": "basic|intermediate|advanced",
    "question": str, "eval_criteria": str }

The agent first selects from the static bank (no LLM needed), then optionally
augments with LLM-generated questions that are JD-specific.
"""

import logging
import uuid
from typing import Dict, List

from app.llm import generate_json
from app.graph.state import InvestmentJobState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Static question bank
# ---------------------------------------------------------------------------

_TECH_CORE: List[dict] = [
    # ── Valuation ──────────────────────────────────────────────────────────
    {"category": "valuation", "difficulty": "basic",
     "question": "请解释 P/E、P/B、EV/EBITDA 三个估值倍数各自适用的场景及局限性。",
     "eval_criteria": "能区分盈利驱动型 vs 资产驱动型行业；提到 EBITDA 忽略资本开支的局限"},
    {"category": "valuation", "difficulty": "intermediate",
     "question": "Walk me through a DCF. Which assumptions move the valuation most?",
     "eval_criteria": "Terminal value weight, WACC sensitivity, FCF definition correctness"},
    {"category": "valuation", "difficulty": "advanced",
     "question": "How would you value a pre-revenue biotech company in Hong Kong?",
     "eval_criteria": "rNPV / probability-weighted pipeline, comparable transaction multiples, burn rate"},
    {"category": "valuation", "difficulty": "intermediate",
     "question": "什么情况下 P/S 比 P/E 更有参考价值？举一个具体行业例子。",
     "eval_criteria": "SaaS/高增长科技/亏损期公司；能举出 A股或港股具体公司"},
    # ── Financial modelling ────────────────────────────────────────────────
    {"category": "modelling", "difficulty": "basic",
     "question": "三张财务报表之间的勾稽关系是什么？净利润变化如何传导到现金流量表？",
     "eval_criteria": "净利润→留存收益→资产负债表；折旧/摊销/营运资本变化加回"},
    {"category": "modelling", "difficulty": "intermediate",
     "question": "如何在模型中处理商誉减值对三张报表的影响？",
     "eval_criteria": "利润表计费→资产负债表商誉减少→现金流量表无现金影响"},
    {"category": "modelling", "difficulty": "advanced",
     "question": "Build a quick LBO model in your head for a company with 10x EBITDA entry, "
                 "5x leverage, 5-year hold. What IRR do you get at 12x exit?",
     "eval_criteria": "Rough IRR ≈ 20-25%; ability to walk through debt paydown and equity return"},
    # ── Sector: Healthcare ─────────────────────────────────────────────────
    {"category": "sector_healthcare", "difficulty": "intermediate",
     "question": "医保谈判如何影响创新药企的收入预测？你在模型里怎么量化这个风险？",
     "eval_criteria": "降价幅度假设、以价换量弹性、医保目录纳入时间点"},
    {"category": "sector_healthcare", "difficulty": "advanced",
     "question": "比较 PD-1 单抗在中美定价的差异，背后的支付体系逻辑是什么？",
     "eval_criteria": "医保 vs 商保覆盖率、HTA vs 谈判机制、价格保密协议"},
    # ── Sector: TMT / AI ───────────────────────────────────────────────────
    {"category": "sector_tmt", "difficulty": "intermediate",
     "question": "How do you model revenue for a Chinese cloud company — "
                 "what are the key line items and growth drivers?",
     "eval_criteria": "IaaS/PaaS/SaaS split, GPU/inference capacity, enterprise vs SME mix"},
    {"category": "sector_tmt", "difficulty": "advanced",
     "question": "AI capex cycle: which parts of the semiconductor supply chain "
                 "are over-earning today and which are under-earning?",
     "eval_criteria": "HBM memory, advanced packaging, CoWoS; cooling, power infra as under-earning"},
    # ── Sector: New Energy ─────────────────────────────────────────────────
    {"category": "sector_new_energy", "difficulty": "intermediate",
     "question": "锂电池产业链中哪个环节的定价权最强？为什么？",
     "eval_criteria": "隔膜 vs 正极 vs 负极 vs 电解液的竞争格局差异"},
    {"category": "sector_new_energy", "difficulty": "advanced",
     "question": "海外储能市场对中国电池企业的增量意义，以及 IRA 法案带来的竞争格局变化。",
     "eval_criteria": "FEOC 限制、本土化产能要求、宁德 vs 比亚迪 vs 海外竞争对手"},
    # ── Macro / Markets ────────────────────────────────────────────────────
    {"category": "macro", "difficulty": "basic",
     "question": "美联储加息周期中，成长股 vs 价值股的相对表现规律是什么？背后逻辑？",
     "eval_criteria": "久期效应：长久期资产贴现率敏感；价值股现金流近端"},
    {"category": "macro", "difficulty": "intermediate",
     "question": "人民币汇率贬值对 A 股出口企业和进口企业的影响分别是什么？",
     "eval_criteria": "收入端（USD计价出口受益）vs 成本端（进口原材料涨价）"},
    # ── Quant / Data ───────────────────────────────────────────────────────
    {"category": "quant", "difficulty": "intermediate",
     "question": "你会如何用 Python 构建一个简单的动量因子回测框架？说明关键步骤。",
     "eval_criteria": "数据获取→信号计算→持仓构建→业绩归因；提到 look-ahead bias 防范"},
    {"category": "quant", "difficulty": "advanced",
     "question": "Factor crowding 是什么？它如何导致因子失效？如何在组合构建中缓解？",
     "eval_criteria": "持仓相似度、流动性冲击、正交化/分散化/容量约束"},
]

_BEHAVIORAL: List[dict] = [
    {"category": "behavioral", "difficulty": "basic",
     "question": "Tell me about yourself in 2 minutes (pitch your background for this role).",
     "eval_criteria": "Clarity, relevance to IB/ER/AM role, specific evidence not generalities"},
    {"category": "behavioral", "difficulty": "basic",
     "question": "为什么选择投研而不是投行或咨询？",
     "eval_criteria": "具体动机（行业理解深度、持续学习、长周期思考）vs 泛化回答"},
    {"category": "behavioral", "difficulty": "intermediate",
     "question": "Describe a time you had a strong conviction view and the market proved you wrong. "
                 "What did you do?",
     "eval_criteria": "自我批判能力、止损纪律、是否更新了框架而不是死守"},
    {"category": "behavioral", "difficulty": "intermediate",
     "question": "你曾经在压力下独立完成过什么研究项目？时间线和输出结果是什么？",
     "eval_criteria": "STAR 结构、量化成果、展示主动性"},
    {"category": "behavioral", "difficulty": "intermediate",
     "question": "How do you prioritize when you have three urgent research deadlines at once?",
     "eval_criteria": "Stakeholder communication, scope triage, quality vs speed trade-off"},
    {"category": "behavioral", "difficulty": "intermediate",
     "question": "Tell me about a research call where you changed your mind. What was the trigger?",
     "eval_criteria": "Intellectual honesty, signal vs noise distinction, update process"},
    {"category": "behavioral", "difficulty": "advanced",
     "question": "你如何保持对市场的独立判断，避免被卖方或新闻牵着走？",
     "eval_criteria": "一手数据来源、逆向思维框架、主动寻找反面证据的习惯"},
    {"category": "behavioral", "difficulty": "advanced",
     "question": "Describe your career plan over the next 5 years in asset management.",
     "eval_criteria": "Realistic progression (analyst→senior→PM), domain specialization plan"},
]

_STOCK_PITCH_DRILLS: List[dict] = [
    {"category": "stock_pitch", "difficulty": "basic",
     "question": "用 SOTP 结构给一家你熟悉的港股公司做一个 3 分钟 pitch。",
     "eval_criteria": "分部估值逻辑清晰、催化剂具体可验证、风险和应对方案"},
    {"category": "stock_pitch", "difficulty": "basic",
     "question": "Pitch a long idea in your sector: thesis (1 sentence), "
                 "3 key drivers, valuation, and top 2 risks with mitigants.",
     "eval_criteria": "Concise thesis; drivers are specific not generic; price target derivation"},
    {"category": "stock_pitch", "difficulty": "intermediate",
     "question": "你的 bull case 和 bear case 分别对应什么假设？概率各是多少？",
     "eval_criteria": "非对称 risk/reward 框架；能量化两种情景下的目标价"},
    {"category": "stock_pitch", "difficulty": "intermediate",
     "question": "What does the market currently have wrong about this stock? "
                 "Why is it a mispricing and not just a value trap?",
     "eval_criteria": "Specific catalyst timeline; why consensus is wrong on a key assumption"},
    {"category": "stock_pitch", "difficulty": "advanced",
     "question": "如果你推荐的股票在未来一个月下跌 15%，你的第一反应是什么？",
     "eval_criteria": "区分价格下跌 vs 基本面恶化；止损纪律 vs 加仓逻辑"},
    {"category": "stock_pitch", "difficulty": "advanced",
     "question": "Pitch a short idea. What's your edge over the market on the bear thesis?",
     "eval_criteria": "Catalyst specificity; borrow cost awareness; stop-loss discipline"},
]


def _tag(entry: dict) -> dict:
    """Add a unique ID to each question."""
    return {"id": str(uuid.uuid4())[:8], **entry}


def _filter_by_sector(questions: List[dict], sector: str) -> List[dict]:
    """Keep all non-sector questions plus sector-specific ones."""
    sector_key = f"sector_{sector.replace(' ', '_').replace('-', '_')}"
    return [
        q for q in questions
        if not q["category"].startswith("sector_") or q["category"] == sector_key
    ]


def question_bank_agent(state: InvestmentJobState) -> Dict[str, dict]:
    jd_profile = state.get("jd_profile") or {}
    job_type = jd_profile.get("job_type", "unknown")
    sector = jd_profile.get("sector", "generalist")
    city = jd_profile.get("city", "unknown")
    hard_reqs = jd_profile.get("hard_requirements", [])

    tech_filtered = _filter_by_sector(_TECH_CORE, sector)
    tech_tagged = [_tag(q) for q in tech_filtered]
    beh_tagged = [_tag(q) for q in _BEHAVIORAL]
    pitch_tagged = [_tag(q) for q in _STOCK_PITCH_DRILLS]

    # Optionally augment with LLM-generated JD-specific questions
    augment_prompt = (
        f"为以下岗位再生成5道技术面试题和3道行为面试题，要求具体可执行。\n"
        f"岗位：{job_type}，行业：{sector}，城市：{city}，核心要求：{hard_reqs}\n"
        "返回 JSON：{{\"extra_technical\": [...], \"extra_behavioral\": [...]}}\n"
        "每题格式：{{\"question\": str, \"eval_criteria\": str}}"
    )
    fallback_aug = {"extra_technical": [], "extra_behavioral": []}
    augmented = generate_json(augment_prompt, fallback_aug)

    for q in augmented.get("extra_technical", []):
        tech_tagged.append(_tag({"category": "jd_specific", "difficulty": "intermediate", **q}))
    for q in augmented.get("extra_behavioral", []):
        beh_tagged.append(_tag({"category": "jd_behavioral", "difficulty": "intermediate", **q}))

    bank = {
        "technical": tech_tagged,
        "behavioral": beh_tagged,
        "stock_pitch_drills": pitch_tagged,
        "meta": {
            "job_type": job_type,
            "sector": sector,
            "city": city,
            "total_questions": len(tech_tagged) + len(beh_tagged) + len(pitch_tagged),
        },
    }
    logger.info(
        "question_bank_agent: %d tech + %d behavioral + %d pitch drills.",
        len(tech_tagged), len(beh_tagged), len(pitch_tagged),
    )
    return {"question_bank": bank}
