CREATE TABLE rag_evaluation_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES rag_experiments(id) ON DELETE CASCADE,
    case_id VARCHAR(120) NOT NULL,
    question TEXT NOT NULL,
    expected_answer TEXT,
    relevant_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    relevant_document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_citation_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    evaluation_top_k INTEGER NOT NULL DEFAULT 5,
    notes TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_rag_evaluation_cases_experiment_case UNIQUE (experiment_id, case_id),
    CONSTRAINT chk_rag_evaluation_cases_top_k CHECK (evaluation_top_k > 0)
);

CREATE INDEX idx_rag_evaluation_cases_experiment_id
    ON rag_evaluation_cases (experiment_id, updated_at DESC);
CREATE INDEX idx_rag_evaluation_cases_status
    ON rag_evaluation_cases (status);
