"""把 data/jd_raw/ 下新增 JD 推送到 GitHub 仓库"""
import base64
import json
from pathlib import Path
from typing import Optional

import requests

from .config import GITHUB_CONFIG

API = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {GITHUB_CONFIG['token']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_remote_sha(remote_path: str) -> Optional[str]:
    """获取远端文件的 SHA（用于更新时携带）"""
    owner = GITHUB_CONFIG["owner"]
    repo = GITHUB_CONFIG["repo"]
    branch = GITHUB_CONFIG["branch"]
    url = f"{API}/repos/{owner}/{repo}/contents/{remote_path}?ref={branch}"
    resp = requests.get(url, headers=_headers(), timeout=10)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


def push_file(local_path: Path, remote_path: str, commit_msg: str) -> bool:
    """推送单个文件到 GitHub，自动处理新建/更新"""
    owner = GITHUB_CONFIG["owner"]
    repo = GITHUB_CONFIG["repo"]
    branch = GITHUB_CONFIG["branch"]
    url = f"{API}/repos/{owner}/{repo}/contents/{remote_path}"

    content_b64 = base64.b64encode(local_path.read_bytes()).decode()
    sha = _get_remote_sha(remote_path)

    payload = {
        "message": commit_msg,
        "content": content_b64,
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=_headers(), json=payload, timeout=15)
    if resp.status_code in (200, 201):
        print(f"[sync] ✓ {remote_path}")
        return True
    else:
        print(f"[sync] ✗ {remote_path} → {resp.status_code}: {resp.text[:200]}")
        return False


def sync_all(data_dir: Path, dry_run: bool = False) -> int:
    """把 data_dir 里全部 JD 推送到 GitHub data/jd_raw/ 目录"""
    prefix = GITHUB_CONFIG["data_path_prefix"]
    pushed = 0
    for f in sorted(data_dir.glob("*.json")):
        remote_path = f"{prefix}/{f.name}"
        if dry_run:
            print(f"[dry-run] {remote_path}")
            pushed += 1
            continue
        ok = push_file(
            local_path=f,
            remote_path=remote_path,
            commit_msg=f"data: add JD {f.stem}",
        )
        if ok:
            pushed += 1
    print(f"[sync] 推送完成: {pushed}/{len(list(data_dir.glob('*.json')))} 条")
    return pushed
