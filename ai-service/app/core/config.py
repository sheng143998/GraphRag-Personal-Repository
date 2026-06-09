import os
import re
from dataclasses import dataclass
from urllib.parse import quote_plus
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()

def _build_database_url() -> str:
    db_url = os.getenv("DB_URL", "")
    if db_url:
        m = re.match(r"jdbc:postgresql://([^:/]+)(?::(\d+))?/([^?]+)", db_url)
        if not m:
            return ""
        host = m.group(1)
        port = m.group(2) or "5432"
        dbname = m.group(3)
        user = os.getenv("DB_USERNAME", "postgres")
        password = os.getenv("DB_PASSWORD", "")
        if password:
            return f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{dbname}"
        return f"postgresql://{quote_plus(user)}@{host}:{port}/{dbname}"
    return ""


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name, "")
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name, "")
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, "")
    if not value.strip():
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI Service"
    app_version: str = "0.1.0"
    default_strategy: str = "basic-rag"
    default_prompt_name: str = "rag_answer"
    default_prompt_version: str = "v1"
    default_embedding_model: str = "stub-embedding"
    default_llm_model: str = "stub-llm"
    default_rerank_model: str = "stub-rerank"
    mineru_api_base_url: str = "https://mineru.net/api/v1/agent"
    mineru_api_token: str = ""
    database_url: str = ""
    rag_use_database: bool = True

    model_provider: str = "stub"
    model_base_url: str = ""
    model_api_key: str = ""
    model_timeout_seconds: float = 60.0
    model_max_retries: int = 2

    llm_provider: str = "stub"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_temperature: float = 0.2
    llm_max_tokens: int = 4096

    embedding_provider: str = "stub"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 10

    rerank_provider: str = "stub"
    rerank_base_url: str = ""
    rerank_api_key: str = ""
    rerank_top_n: int = 10


_model_provider = os.getenv("MODEL_PROVIDER", "stub")
_model_base_url = os.getenv("MODEL_BASE_URL", "")
_model_api_key = os.getenv("MODEL_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")

_llm_model = os.getenv("LLM_MODEL") or os.getenv("DEFAULT_LLM_MODEL") or "stub-llm"
_embedding_model = os.getenv("EMBEDDING_MODEL") or os.getenv("DEFAULT_EMBEDDING_MODEL") or "stub-embedding"
_rerank_model = os.getenv("RERANK_MODEL") or os.getenv("DEFAULT_RERANK_MODEL") or "stub-rerank"

settings = Settings(
    database_url=_build_database_url(),
    rag_use_database=_env_bool("AI_RAG_USE_DATABASE", True),
    mineru_api_base_url=os.getenv("MINERU_API_BASE_URL", "https://mineru.net/api/v1/agent"),
    mineru_api_token=os.getenv("MINERU_API_TOKEN", ""),
    default_llm_model=_llm_model,
    default_embedding_model=_embedding_model,
    default_rerank_model=_rerank_model,
    model_provider=_model_provider,
    model_base_url=_model_base_url,
    model_api_key=_model_api_key,
    model_timeout_seconds=_env_float("MODEL_TIMEOUT_SECONDS", 60.0),
    model_max_retries=_env_int("MODEL_MAX_RETRIES", 2),
    llm_provider=os.getenv("LLM_PROVIDER", _model_provider),
    llm_base_url=os.getenv("LLM_BASE_URL", _model_base_url or os.getenv("OPENAI_BASE_URL", "")),
    llm_api_key=os.getenv("LLM_API_KEY", _model_api_key),
    llm_temperature=_env_float("LLM_TEMPERATURE", 0.2),
    llm_max_tokens=_env_int("LLM_MAX_TOKENS", 4096),
    embedding_provider=os.getenv("EMBEDDING_PROVIDER", _model_provider),
    embedding_base_url=os.getenv("EMBEDDING_BASE_URL", _model_base_url or os.getenv("OPENAI_BASE_URL", "")),
    embedding_api_key=os.getenv("EMBEDDING_API_KEY", _model_api_key),
    embedding_dimensions=_env_int("EMBEDDING_DIMENSIONS", 1536),
    embedding_batch_size=_env_int("EMBEDDING_BATCH_SIZE", 10),
    rerank_provider=os.getenv("RERANK_PROVIDER", _model_provider),
    rerank_base_url=os.getenv("RERANK_BASE_URL", _model_base_url or os.getenv("OPENAI_BASE_URL", "")),
    rerank_api_key=os.getenv("RERANK_API_KEY", _model_api_key),
    rerank_top_n=_env_int("RERANK_TOP_N", 10),
)
