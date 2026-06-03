"""JD 文本 → 结构化字段（role_type, skills, requirements, location）"""
import json
import re
from pathlib import Path
from typing import Optional

from ..config.role_taxonomy import ROLE_TAXONOMY  # 复用已有 taxonomy

# ── 简单规则提取（无 LLM 依赖，快速 MVP） ─────────────

SKILL_KEYWORDS = {
    "python": ["python", "pandas", "numpy", "scipy"],
    "sql": ["sql", "mysql", "postgresql", "database"],
    "excel": ["excel", "vba", "spreadsheet"],
    "modeling": ["financial model", "dcf", "lbo", "valuation"],
    "bloomberg": ["bloomberg", "wind", "refinitiv", "factset"],
    "statistics": ["statistics", "econometrics", "regression", "machine learning"],
    "mandarin": ["mandarin", "chinese", "普通话", "中文"],
    "cantonese": ["cantonese", "粤语"],
    "english": ["english", "英语", "cfa", "ielts"],
    "research": ["research report", "industry report", "调研", "研报"],
}


def detect_role_type(text: str) -> str:
    """用 role_taxonomy 关键字粗分岗位类型"""
    text_lower = text.lower()
    for role_type, meta in ROLE_TAXONOMY.items():
        for kw in meta.get("keywords", []):
            if kw.lower() in text_lower:
                return role_type
    return "unknown"


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill, kws in SKILL_KEYWORDS.items():
        if any(kw in text_lower for kw in kws):
            found.append(skill)
    return found


def extract_location(text: str) -> Optional[str]:
    locations = ["Hong Kong", "Shanghai", "Beijing", "Singapore", "London", "New York"]
    for loc in locations:
        if loc.lower() in text.lower():
            return loc
    return None


def extract_degree(text: str) -> Optional[str]:
    text_lower = text.lower()
    if any(w in text_lower for w in ["phd", "doctorate"]):
        return "PhD"
    if any(w in text_lower for w in ["master", "msc", "mba", "研究生"]):
        return "Master"
    if any(w in text_lower for w in ["bachelor", "undergraduate", "本科"]):
        return "Bachelor"
    return None


def parse_jd(raw: dict) -> dict:
    text = raw.get("raw_text", "")
    parsed = {
        **raw,
        "role_type": detect_role_type(text),
        "skills": extract_skills(text),
        "location_detected": extract_location(text),
        "degree_required": extract_degree(text),
        "parsed": True,
    }
    return parsed


def parse_all_pending(data_dir: Path) -> int:
    """扫描 data_dir 中 parsed=False 的文件，解析并原地更新"""
    count = 0
    for f in data_dir.glob("*.json"):
        raw = json.loads(f.read_text())
        if raw.get("parsed"):
            continue
        parsed = parse_jd(raw)
        f.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
        count += 1
    print(f"[parser] 解析完成: {count} 条")
    return count
