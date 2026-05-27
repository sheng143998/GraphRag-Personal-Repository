import os
from dataclasses import dataclass


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
    database_url: str = ""
    rag_use_database: bool = True


settings = Settings(
    database_url=os.getenv("AI_DATABASE_URL") or os.getenv("DATABASE_URL") or "",
    rag_use_database=os.getenv("AI_RAG_USE_DATABASE", "true").lower() in {"1", "true", "yes", "on"},
)
