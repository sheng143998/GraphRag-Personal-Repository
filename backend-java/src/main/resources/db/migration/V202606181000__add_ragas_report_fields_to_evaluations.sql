ALTER TABLE rag_experiment_evaluations
    ADD COLUMN ragas_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN ragas_metric_names JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN ragas_version VARCHAR(80),
    ADD COLUMN ragas_judge_model VARCHAR(160),
    ADD COLUMN ragas_report_uri TEXT;
