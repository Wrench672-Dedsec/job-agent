import argparse
import json
import os
from pathlib import Path

from app.graph.graph import build_graph


def _read_text(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run job agent flow")
    parser.add_argument("--resume", help="Path to resume text")
    parser.add_argument("--jd", help="Path to JD text")
    parser.add_argument("--target-city", default="")
    parser.add_argument("--target-sector", default="")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "mock"))
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "llama3.1:8b"))
    args = parser.parse_args()

    os.environ["LLM_PROVIDER"] = args.provider
    os.environ["LLM_MODEL"] = args.model

    state = {
        "resume_text": _read_text(args.resume),
        "jd_text": _read_text(args.jd),
        "target_city": args.target_city,
        "target_sector": args.target_sector,
    }

    graph = build_graph()
    result = graph.invoke(state)
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
