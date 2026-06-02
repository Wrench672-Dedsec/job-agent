from typing import Dict, List
import json
from pathlib import Path

from app.config import settings
from app.graph.state import InvestmentJobState


def _load_cases(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def rag_agent(state: InvestmentJobState) -> Dict[str, List[dict]]:
    cases = _load_cases(settings.rag_cases_path)
    return {"rag_cases": cases[:5]}
