"""多源 JD 抓取：手动粘贴 / Apify / RSS"""
import hashlib
import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from .config import APIFY_TOKEN, DATA_DIR, SOURCES, TARGET_LOCATIONS, TARGET_ROLES


def _jd_id(text: str) -> str:
    """用文本 hash 作为唯一 ID，避免重复"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _save(jd: dict) -> Optional[Path]:
    """写入 data/jd_raw/<id>.json，已存在则跳过"""
    path = DATA_DIR / f"{jd['id']}.json"
    if path.exists():
        return None
    path.write_text(json.dumps(jd, ensure_ascii=False, indent=2))
    return path


# ── 1. 手动粘贴 ───────────────────────────────────────
def fetch_manual() -> list[dict]:
    """交互式粘贴 JD，回车两次结束"""
    print("\n[手动模式] 粘贴 JD 文本（空行结束）：")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if not text:
        return []
    jd = {
        "id": _jd_id(text),
        "source": "manual",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_text": text,
        "parsed": False,
    }
    saved = _save(jd)
    return [jd] if saved else []


# ── 2. Apify ──────────────────────────────────────────
def fetch_apify() -> list[dict]:
    """调用 Apify LinkedIn Jobs Scraper"""
    cfg = SOURCES["apify"]
    if not cfg["enabled"]:
        return []

    results = []
    for role in TARGET_ROLES[:5]:  # 限制 API 调用量
        for loc in TARGET_LOCATIONS[:2]:
            url = "https://api.apify.com/v2/acts/{actor}/runs".format(**cfg)
            payload = {
                "searchTerms": [role],
                "location": loc,
                "maxResults": cfg["max_items"],
            }
            headers = {"Authorization": f"Bearer {cfg['token']}"}
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
                run_id = resp.json()["data"]["id"]
                # 轮询结果（最多等 60s）
                for _ in range(12):
                    time.sleep(5)
                    data_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items"
                    items = requests.get(data_url, headers=headers, timeout=30).json()
                    if items:
                        break
                for item in items:
                    text = item.get("description", "")
                    if not text:
                        continue
                    jd = {
                        "id": _jd_id(text),
                        "source": "apify_linkedin",
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                        "title": item.get("title"),
                        "company": item.get("companyName"),
                        "location": item.get("location"),
                        "url": item.get("url"),
                        "raw_text": text,
                        "parsed": False,
                    }
                    saved = _save(jd)
                    if saved:
                        results.append(jd)
            except Exception as e:
                print(f"[Apify] 请求失败 role={role} loc={loc}: {e}")
    return results


# ── 3. RSS ────────────────────────────────────────────
def fetch_rss() -> list[dict]:
    """解析公开 RSS 聚合源（合规）"""
    cfg = SOURCES["rss"]
    if not cfg["enabled"]:
        return []

    results = []
    for feed_url in cfg["feeds"]:
        try:
            resp = requests.get(feed_url, timeout=15)
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item"):
                title = (item.findtext("title") or "").strip()
                desc = (item.findtext("description") or "").strip()
                link = (item.findtext("link") or "").strip()
                text = f"{title}\n{desc}"
                jd = {
                    "id": _jd_id(text),
                    "source": "rss",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "title": title,
                    "url": link,
                    "raw_text": text,
                    "parsed": False,
                }
                saved = _save(jd)
                if saved:
                    results.append(jd)
        except Exception as e:
            print(f"[RSS] 解析失败 {feed_url}: {e}")
    return results


def fetch_all() -> list[dict]:
    """运行所有已启用的数据源"""
    results = []
    results += fetch_rss()
    results += fetch_apify()
    print(f"[fetcher] 新增 JD: {len(results)} 条")
    return results
