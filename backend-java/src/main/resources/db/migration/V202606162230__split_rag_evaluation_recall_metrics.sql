ALTER TABLE rag_evaluation_cases
    ADD COLUMN required_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN supporting_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN acceptable_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN citation_chunk_ids JSONB NOT NULL DEFAULT '[]'::jsonb;

UPDATE rag_evaluation_cases
SET required_chunk_ids = relevant_chunk_ids
WHERE required_chunk_ids = '[]'::jsonb
  AND relevant_chunk_ids <> '[]'::jsonb;

UPDATE rag_evaluation_cases
SET citation_chunk_ids = expected_citation_chunk_ids
WHERE citation_chunk_ids = '[]'::jsonb
  AND expected_citation_chunk_ids <> '[]'::jsonb;

ALTER TABLE rag_experiment_evaluations
    ADD COLUMN chunk_recall_at_k DOUBLE PRECISION,
    ADD COLUMN document_recall_at_k DOUBLE PRECISION,
    ADD COLUMN evidence_recall_at_k DOUBLE PRECISION;

UPDATE rag_experiment_evaluations
SET evidence_recall_at_k = recall_at_k
WHERE evidence_recall_at_k IS NULL
  AND recall_at_k IS NOT NULL;
