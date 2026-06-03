"""基于 SHA-256 hash 的 JD 去重"""
import hashlib
import json
from pathlib import Path


def build_seen_set(data_dir: Path) -> set[str]:
    """读取已有 JD 的 id 集合"""
    return {f.stem for f in data_dir.glob("*.json")}


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def is_duplicate(jd_id: str, seen: set[str]) -> bool:
    return jd_id in seen


def remove_duplicates(data_dir: Path) -> int:
    """扫描全量文件，删除 raw_text 完全相同的重复 JD"""
    seen_hashes: dict[str, str] = {}  # hash → file path
    removed = 0
    for f in sorted(data_dir.glob("*.json")):
        jd = json.loads(f.read_text())
        h = text_hash(jd.get("raw_text", ""))
        if h in seen_hashes:
            f.unlink()
            removed += 1
        else:
            seen_hashes[h] = str(f)
    print(f"[dedup] 删除重复 JD: {removed} 条")
    return removed
