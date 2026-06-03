"""interview_map agent

从 jd_profile + question_bank 生成结构化面试地图：
  - 按岗位类型划分 3 轮面试
  - 每轮挂载对应题组 + follow-up 追问
  - 输出 mock_plan（题数 / 预计分钟 / 建议顺序）

写入 state["interview_map"]
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.llm import generate_text


# ── 岗位 → 轮次模板 ────────────────────────────────────────────────────────

ROUND_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "buyside_research": [
        {
            "round": 1,
            "label": "Stock Pitch",
            "modules": ["stock_pitch_drills"],
            "focus": "候选人能否在 5 分钟内完整表达 investment thesis、catalyst、风险",
            "follow_ups": [
                "如果你的 thesis 是错的，最可能在哪个假设出了问题？",
                "你的目标价是怎么算出来的？对哪个变量最敏感？",
                "你的主要竞争对手是谁？他们为什么不是 buy？",
            ],
        },
        {
            "round": 2,
            "label": "Thesis Grill",
            "modules": ["technical"],
            "focus": "深挖财务建模与行业判断，考察候选人压力下是否仍能捍卫观点",
            "follow_ups": [
                "EV/EBITDA 倍数你怎么选的 peer group？",
                "这个公司的 FCF conversion 为什么比同业低？",
                "如果明天发一份利空研报，你会怎么反驳？",
                "你 hedge 这个 position 会怎么做？",
            ],
        },
        {
            "round": 3,
            "label": "Fit & Culture",
            "modules": ["behavioral"],
            "focus": "动机真实性、抗压能力、团队协作与长期发展意愿",
            "follow_ups": [
                "你为什么选 buy-side 而不是 sell-side research？",
                "说一个你判断错误的投资案例，你学到了什么？",
                "你理想中一天的 research analyst 工作是什么样的？",
            ],
        },
    ],
    "quant_research": [
        {
            "round": 1,
            "label": "Technical / Coding",
            "modules": ["technical"],
            "focus": "Python / SQL 实操、统计基础、因子构建逻辑",
            "follow_ups": [
                "手写一个 rolling Sharpe ratio（pandas）",
                "解释 p-hacking，你在自己的回测里怎么防止？",
                "你的因子在换手率 vs. 收益 trade-off 上怎么调参？",
            ],
        },
        {
            "round": 2,
            "label": "Project Deep Dive",
            "modules": ["technical", "stock_pitch_drills"],
            "focus": "从候选人已有项目出发，追问方法论选择、局限性、可改进点",
            "follow_ups": [
                "你选 XGBoost 而不是线性模型的理由是？",
                "样本外测试结果和样本内差多少？你怎么解释这个 gap？",
                "如果数据量增加 10 倍，你的方案哪里会 break？",
                "你的 alpha decay 大概在什么周期？",
            ],
        },
        {
            "round": 3,
            "label": "Fit & Motivation",
            "modules": ["behavioral"],
            "focus": "量化思维与金融直觉的结合，职业规划清晰度",
            "follow_ups": [
                "你觉得纯 systematic 策略的局限在哪里？",
                "你怎么看 ML 在低频因子里的适用性？",
                "5 年后你想做 PM 还是继续 researcher？为什么？",
            ],
        },
    ],
    "sales_trading": [
        {
            "round": 1,
            "label": "Markets & Macro",
            "modules": ["technical"],
            "focus": "对当前市场的理解、宏观感知力、快速反应能力",
            "follow_ups": [
                "今天美债 10Y 大概在哪？背后驱动是什么？",
                "如果美联储明天突然降息 50bp，你会怎么交易？",
                "你最近关注的一个 macro trade idea 是什么？",
            ],
        },
        {
            "round": 2,
            "label": "Product Knowledge",
            "modules": ["technical", "stock_pitch_drills"],
            "focus": "产品定价、风险度量、客户视角",
            "follow_ups": [
                "解释一下 delta hedging 的基本逻辑",
                "一个 EM 客户想买 USD/CNH NDF，你怎么报价？",
                "VaR 的局限性是什么？你会用什么补充？",
            ],
        },
        {
            "round": 3,
            "label": "Fit & Pressure Test",
            "modules": ["behavioral"],
            "focus": "高压下决策质量、自我认知、对交易台文化的适应性",
            "follow_ups": [
                "你做过最糟糕的一个决定是什么？",
                "你怎么在信息不完整时做决定？",
                "你能接受重复性很高的工作（booking / hedging）吗？",
            ],
        },
    ],
    "ibd_pe_vc": [
        {
            "round": 1,
            "label": "Technical (Modeling)",
            "modules": ["technical"],
            "focus": "DCF / LBO / Comps 基础，数字敏感度，会计联动",
            "follow_ups": [
                "DCF 里 terminal value 用 Gordon Growth，g 你怎么选？",
                "折旧增加 100，Net Income / FCF / Cash 各变多少？",
                "LBO 里 PIK toggle note 是怎么回事？",
                "Enterprise Value 和 Equity Value 的 bridge 是什么？",
                "你的 LBO model 里 IRR 对 exit multiple 的敏感度大概是多少？",
            ],
        },
        {
            "round": 2,
            "label": "Deal / Case Discussion",
            "modules": ["technical", "stock_pitch_drills"],
            "focus": "从真实案例或 prompt case 出发，考察行业判断和投资逻辑",
            "follow_ups": [
                "这个 target 最大的风险是什么？你会要求多少 risk premium？",
                "你作为 buyer 的 walk-away price 是多少？怎么算的？",
                "如果对手方出价高 15%，你会怎么建议 client？",
                "你怎么做行业 channel check？",
            ],
        },
        {
            "round": 3,
            "label": "Fit & Motivation",
            "modules": ["behavioral"],
            "focus": "动机、韧性、对高强度工作的认知，文化匹配度",
            "follow_ups": [
                "说一个你说服别人改变主意的例子",
                "你怎么在 deadline 下处理多个优先级冲突的任务？",
                "你为什么选 IBD 而不是直接去 PE？",
            ],
        },
    ],
    "wealth_management": [
        {
            "round": 1,
            "label": "Product & Market",
            "modules": ["technical"],
            "focus": "资产配置逻辑、产品知识、宏观理解",
            "follow_ups": [
                "当前宏观环境下你会怎么配置一个 $10M 账户？",
                "Fixed income 和 equity 的 correlation 在 2022 为什么失效了？",
                "Structured product 里 autocallable 的 payoff 是怎么工作的？",
            ],
        },
        {
            "round": 2,
            "label": "Client Scenario",
            "modules": ["behavioral", "technical"],
            "focus": "客户沟通能力、情景模拟、objection handling",
            "follow_ups": [
                "客户说'我不想承担任何风险'，你怎么回应？",
                "你的一个推荐亏了 20%，客户要求赎回，你怎么处理？",
                "如何向高净值客户解释 fee structure？",
            ],
        },
        {
            "round": 3,
            "label": "Fit",
            "modules": ["behavioral"],
            "focus": "长期服务意识、自我驱动力、对 HNW client 文化的认知",
            "follow_ups": [
                "你为什么想做 wealth management 而不是 research？",
                "你怎么建立和维护客户信任？",
            ],
        },
    ],
}

# 默认模板（未知岗位类型）
DEFAULT_ROUNDS = [
    {"round": 1, "label": "Technical", "modules": ["technical"],
     "focus": "专业技能与硬知识",
     "follow_ups": ["请详细解释你用到的核心方法论", "这个方法的局限性是什么？"]},
    {"round": 2, "label": "Case / Project", "modules": ["technical", "stock_pitch_drills"],
     "focus": "过往项目深挖",
     "follow_ups": ["如果重做，你会改哪个决策？", "这个项目的商业价值是什么？"]},
    {"round": 3, "label": "Behavioral / Fit", "modules": ["behavioral"],
     "focus": "价值观与职业动机",
     "follow_ups": ["说一个你失败的例子和你的反思", "5 年后你希望自己在做什么？"]},
]


# ── 从 question_bank 按模块取题 ─────────────────────────────────────────────

def _pick_questions(
    bank: Dict[str, Any],
    modules: List[str],
    max_per_module: int = 3,
) -> List[Dict[str, Any]]:
    """从 question_bank 的对应 key 中提取题目，保持 [{q, type, eval}] 格式"""
    questions: List[Dict[str, Any]] = []
    for mod in modules:
        items = bank.get(mod, [])
        if isinstance(items, list):
            questions.extend(items[:max_per_module])
        elif isinstance(items, dict):
            # stock_pitch_drills 可能是 {company: [questions]}
            for v in items.values():
                if isinstance(v, list):
                    questions.extend(v[:max_per_module])
                    break
    return questions


# ── mock plan 计算 ────────────────────────────────────────────────────────────

MINUTES_PER_QUESTION = 4  # 平均每题（含追问）4 分钟


def _build_mock_plan(rounds: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_q = sum(len(r.get("questions", [])) + len(r.get("follow_ups", [])) for r in rounds)
    total_min = total_q * MINUTES_PER_QUESTION
    return {
        "total_questions": total_q,
        "estimated_minutes": total_min,
        "round_breakdown": [
            {
                "round": r["round"],
                "label": r["label"],
                "questions": len(r.get("questions", [])),
                "follow_ups": len(r.get("follow_ups", [])),
                "minutes": (
                    len(r.get("questions", [])) + len(r.get("follow_ups", []))
                ) * MINUTES_PER_QUESTION,
            }
            for r in rounds
        ],
        "session_order": [
            f"Round {r['round']}: {r['label']}" for r in rounds
        ],
    }


# ── agent 入口 ─────────────────────────────────────────────────────────────────

def interview_map_agent(state: dict) -> Dict[str, Any]:
    """langgraph node: interview_map

    Input  state keys: jd_profile, question_bank
    Output state keys: interview_map
    """
    jd_profile: Dict[str, Any] = state.get("jd_profile") or {}
    question_bank: Dict[str, Any] = state.get("question_bank") or {}

    job_type: str = jd_profile.get("job_type", "unknown").lower().replace(" ", "_")
    city: str = jd_profile.get("city", "")
    sector: str = jd_profile.get("sector", "")

    # 1. 选轮次模板
    round_template = ROUND_TEMPLATES.get(job_type, DEFAULT_ROUNDS)

    # 2. 给每轮注入真实题目（从 question_bank 取）
    rounds_with_questions = []
    for round_def in round_template:
        qs = _pick_questions(question_bank, round_def["modules"])
        rounds_with_questions.append({
            **round_def,
            "questions": qs,
        })

    # 3. 生成 mock plan
    mock_plan = _build_mock_plan(rounds_with_questions)

    # 4. LLM 生成面试官视角的 coaching tips（可选，fallback 安全）
    tip_prompt = (
        f"岗位类型：{job_type}，城市：{city}，行业：{sector}\n"
        f"面试共 {len(rounds_with_questions)} 轮，"
        f"总题量 {mock_plan['total_questions']} 道，"
        f"预计 {mock_plan['estimated_minutes']} 分钟。\n"
        "请以面试官视角，用 3 句话指出这类岗位面试中候选人最常犯的 3 个错误，"
        "以及 1 个能让候选人脱颖而出的具体建议。输出中文，简洁直接。"
    )
    coaching_tips = generate_text(
        tip_prompt,
        fallback=(
            "1. 回答太宽泛，缺乏具体数字支撑。\n"
            "2. Stock pitch 只讲 thesis，不主动提风险。\n"
            "3. Behavioral 问题没有 STAR 结构。\n"
            "加分：主动引用真实数据或自己的 research 结论。"
        ),
    )

    interview_map = {
        "job_type": job_type,
        "city": city,
        "sector": sector,
        "rounds": rounds_with_questions,
        "mock_plan": mock_plan,
        "coaching_tips": coaching_tips,
    }

    return {"interview_map": interview_map}
