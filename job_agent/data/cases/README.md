# Case Library

本目录存放结构化的求职案例，用于 RAG 检索增强生成。

## 文件说明

| 文件 | 来源 | 案例数 | 说明 |
|------|------|--------|------|
| `wst_osg_cases.json` | WST + OSG 公众号 | 9 | 初始案例库，涵盖IBD/PE/VC/S&T/量化私募方向 |

## Schema 说明

每条案例包含以下字段：

```json
{
  "case_id": "唯一标识符",
  "source": "来源机构（WST/OSG/ACE等）",
  "candidate": {
    "school": "学校",
    "degree": "学位",
    "graduation_year": "毕业年份",
    "major": "专业",
    "location": "所在地",
    "internships": ["已有实习列表"],
    "target_role": "目标岗位",
    "target_industry": "目标行业"
  },
  "problem_type": ["问题标签列表"],
  "initial_diagnosis": "顾问初始诊断",
  "interventions": ["干预措施列表"],
  "outcome": "最终结果",
  "key_insight": "核心洞见",
  "evidence_chunks": ["原文证据片段"]
}
```

## 已覆盖的 problem_type 标签

- 技术基础薄弱
- 职业方向不明确
- 行为面薄弱
- 简历背景碎片化
- Networking话术错误
- 面试框架缺失
- 缺乏量化实战经验
- 投递节奏混乱
- 技术表达弱
- 回测方法理解不足
- 背景院校竞争压力大
- 缺乏S&T行业认知
- 面试前焦虑
- 职业方向模糊
- 简历叙事弱以课程为主
- 求职节奏无规划
- 买方知识体系需从零构建
- Stock pitch能力不足
- 简历优势展示不足
- 金融基础为零数学背景转金融
- 个人故事表达不足
- 行业赛道认知空白
- 双专业背景定位模糊
- 对冲基金知识体系为零
- 经历零散无主线叙事
- 自我介绍变流水账
- 信息差导致低效求职
- 不会讲故事

## 扩充说明

后续添加案例时，请遵循同一 schema，并更新此 README 中的文件说明表格。
建议每新增 10 条案例从中抽取 2-3 条加入 `gold_set/` 目录作为评测基准。
