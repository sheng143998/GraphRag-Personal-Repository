ALTER TABLE rag_experiment_evaluations
    ADD COLUMN recall_at_k DOUBLE PRECISION,
    ADD COLUMN precision_at_k DOUBLE PRECISION,
    ADD COLUMN mrr DOUBLE PRECISION,
    ADD COLUMN citation_hit DOUBLE PRECISION,
    ADD COLUMN graph_entity_coverage DOUBLE PRECISION,
    ADD COLUMN graph_relationship_hit DOUBLE PRECISION,
    ADD COLUMN graph_expansion_term_hit DOUBLE PRECISION,
    ADD COLUMN latency_ms BIGINT,
    ADD COLUMN strategy_config JSONB NOT NULL DEFAULT '{}'::jsonb;
