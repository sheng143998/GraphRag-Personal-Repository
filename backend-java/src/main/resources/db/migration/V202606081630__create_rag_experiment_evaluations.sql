CREATE TABLE rag_experiment_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES rag_experiments(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES rag_runs(id) ON DELETE CASCADE,
    grounded_score DOUBLE PRECISION,
    retrieval_score DOUBLE PRECISION,
    expected_answer TEXT,
    generated_answer TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rag_experiment_evaluations_experiment_created
    ON rag_experiment_evaluations (experiment_id, created_at DESC);
CREATE INDEX idx_rag_experiment_evaluations_run_id
    ON rag_experiment_evaluations (run_id);
