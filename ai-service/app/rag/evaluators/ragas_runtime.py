from __future__ import annotations

from app.core.config import settings


def build_langchain_generation_models():
    """Build LangChain models for optional RAGAS TestsetGenerator runtime.

    Keep this module off the FastAPI hot path. It is imported only by the
    offline testset generation script when --generator-mode ragas is selected.
    """

    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    except Exception as exc:  # pragma: no cover - optional isolated runtime
        raise RuntimeError(
            "RAGAS generation requires langchain-openai in the isolated RAGAS environment."
        ) from exc

    if not settings.llm_base_url or not settings.llm_api_key or not settings.default_llm_model:
        raise RuntimeError("Missing LLM_BASE_URL, LLM_API_KEY, or DEFAULT_LLM_MODEL for RAGAS generation.")
    if not settings.embedding_base_url or not settings.embedding_api_key or not settings.default_embedding_model:
        raise RuntimeError(
            "Missing EMBEDDING_BASE_URL, EMBEDDING_API_KEY, or DEFAULT_EMBEDDING_MODEL for RAGAS generation."
        )

    llm = ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.default_llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.model_timeout_seconds,
        max_retries=settings.model_max_retries,
    )
    embeddings = OpenAIEmbeddings(
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key,
        model=settings.default_embedding_model,
        dimensions=settings.embedding_dimensions,
        timeout=settings.model_timeout_seconds,
        max_retries=settings.model_max_retries,
    )
    return llm, embeddings
