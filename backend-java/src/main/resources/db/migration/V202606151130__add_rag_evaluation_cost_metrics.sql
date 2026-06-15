ALTER TABLE rag_experiment_evaluations
    ADD COLUMN prompt_tokens INTEGER,
    ADD COLUMN completion_tokens INTEGER,
    ADD COLUMN total_tokens INTEGER,
    ADD COLUMN embedding_tokens INTEGER,
    ADD COLUMN rerank_tokens INTEGER,
    ADD COLUMN estimated_cost DOUBLE PRECISION,
    ADD COLUMN embedding_latency_ms BIGINT,
    ADD COLUMN retrieval_latency_ms BIGINT,
    ADD COLUMN rerank_latency_ms BIGINT,
    ADD COLUMN llm_latency_ms BIGINT,
    ADD COLUMN token_usage JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN latency_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb;
