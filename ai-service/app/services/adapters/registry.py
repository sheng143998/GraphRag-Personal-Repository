from app.core.config import settings
from app.services.adapters.openai_compatible import (
    OpenAICompatibleEmbeddingAdapter,
    OpenAICompatibleLLMAdapter,
    OpenAICompatibleRerankAdapter,
)
from app.services.adapters.stub import StubEmbeddingAdapter, StubLLMAdapter, StubRerankAdapter


def _is_openai_compatible(provider: str) -> bool:
    return provider.lower() in {"openai-compatible", "openai", "dashscope-compatible"}


def _has_required_config(*values: str) -> bool:
    return all(value is not None and str(value).strip() for value in values)


def _build_llm_adapter():
    if _is_openai_compatible(settings.llm_provider) and _has_required_config(
        settings.llm_base_url,
        settings.llm_api_key,
        settings.default_llm_model,
    ):
        return OpenAICompatibleLLMAdapter(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.default_llm_model,
            timeout_seconds=settings.model_timeout_seconds,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            max_retries=settings.model_max_retries,
        )
    return StubLLMAdapter()


def _build_embedding_adapter():
    if _is_openai_compatible(settings.embedding_provider) and _has_required_config(
        settings.embedding_base_url,
        settings.embedding_api_key,
        settings.default_embedding_model,
    ):
        return OpenAICompatibleEmbeddingAdapter(
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key,
            model=settings.default_embedding_model,
            timeout_seconds=settings.model_timeout_seconds,
            dimensions=settings.embedding_dimensions,
            batch_size=settings.embedding_batch_size,
            max_retries=settings.model_max_retries,
        )
    return StubEmbeddingAdapter()


def _build_rerank_adapter():
    if _is_openai_compatible(settings.rerank_provider) and _has_required_config(
        settings.rerank_base_url,
        settings.rerank_api_key,
        settings.default_rerank_model,
    ):
        return OpenAICompatibleRerankAdapter(
            base_url=settings.rerank_base_url,
            api_key=settings.rerank_api_key,
            model=settings.default_rerank_model,
            timeout_seconds=settings.model_timeout_seconds,
            top_n=settings.rerank_top_n,
            max_retries=settings.model_max_retries,
        )
    return StubRerankAdapter()


llm_adapter = _build_llm_adapter()
embedding_adapter = _build_embedding_adapter()
rerank_adapter = _build_rerank_adapter()


def get_llm_model_name() -> str:
    return settings.default_llm_model


def get_embedding_model_name() -> str:
    return settings.default_embedding_model


def get_rerank_model_name() -> str:
    return settings.default_rerank_model