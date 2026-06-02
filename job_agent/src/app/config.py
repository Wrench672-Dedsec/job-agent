from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT_DIR / "data")).resolve()
DEFAULT_RAG_CASES = Path(
    os.getenv("RAG_CASES_PATH", DATA_DIR / "seed" / "cases.json")
).resolve()


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "dev")
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.1:8b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    data_dir: Path = DATA_DIR
    seed_dir: Path = DATA_DIR / "seed"
    logs_dir: Path = DATA_DIR / "logs"
    rag_cases_path: Path = DEFAULT_RAG_CASES


settings = Settings()
