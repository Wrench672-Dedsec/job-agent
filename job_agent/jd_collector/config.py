"""JD 采集配置：关键字、岗位类型、来源、输出路径"""
import os
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "jd_raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── 目标岗位关键字 ────────────────────────────────────
TARGET_ROLES = [
    "equity research intern",
    "research analyst intern",
    "investment analyst intern",
    "buy side analyst",
    "quant research intern",
    "quant analyst intern",
    "sales trading analyst",
    "investment banking analyst",
    "financial analyst intern",
    "asset management analyst",
    "healthcare analyst intern",
    "pharma equity research",
]

# ── 目标地区 ──────────────────────────────────────────
TARGET_LOCATIONS = ["Hong Kong", "Shanghai", "Beijing", "Singapore"]

# ── 数据源配置 ────────────────────────────────────────
SOURCES = {
    "manual": {"enabled": True},
    "apify": {
        "enabled": bool(os.getenv("APIFY_TOKEN")),
        "token": os.getenv("APIFY_TOKEN", ""),
        "actor": "curious_coder/linkedin-jobs-scraper",
        "max_items": 50,
    },
    "rss": {
        "enabled": True,
        "feeds": [
            # 公开合规的 RSS 聚合源
            "https://www.indeed.com/rss?q=equity+research+intern&l=Hong+Kong",
            "https://www.indeed.com/rss?q=investment+analyst+intern&l=Shanghai",
        ],
    },
}

# ── GitHub 推送配置 ───────────────────────────────────
GITHUB_CONFIG = {
    "token": os.getenv("GITHUB_TOKEN", ""),
    "owner": "Wrench672-Dedsec",
    "repo": "job-agent",
    "branch": "main",
    "data_path_prefix": "data/jd_raw",
}

# ── 调度配置 ──────────────────────────────────────────
SCHEDULE = {
    "hour": 9,
    "minute": 0,
    "timezone": "Asia/Hong_Kong",
}
