from app.core.config import settings
from app.services.adapters.stub import StubEmbeddingAdapter, StubLLMAdapter, StubRerankAdapter


llm_adapter = StubLLMAdapter()
embedding_adapter = StubEmbeddingAdapter()
rerank_adapter = StubRerankAdapter()


def get_llm_model_name() -> str:
    return settings.default_llm_model


def get_embedding_model_name() -> str:
    return settings.default_embedding_model


def get_rerank_model_name() -> str:
    return settings.default_rerank_model
