ALTER TABLE rag_runs
    ADD COLUMN trace_attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN trace_steps JSONB NOT NULL DEFAULT '[]'::jsonb;
