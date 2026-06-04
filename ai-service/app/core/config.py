import os
import re
from dataclasses import dataclass
from urllib.parse import quote_plus


def _build_database_url() -> str:
    url = os.getenv("AI_DATABASE_URL") or os.getenv("DATABASE_URL")
    if url:
        return url
    db_url = os.getenv("DB_URL", "")
    if not db_url:
        return ""
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


settings = Settings(
    database_url=_build_database_url(),
    rag_use_database=os.getenv("AI_RAG_USE_DATABASE", "true").lower() in {"1", "true", "yes", "on"},
    mineru_api_base_url=os.getenv("MINERU_API_BASE_URL", "https://mineru.net/api/v1/agent"),
    mineru_api_token=os.getenv("MINERU_API_TOKEN", ""),
)