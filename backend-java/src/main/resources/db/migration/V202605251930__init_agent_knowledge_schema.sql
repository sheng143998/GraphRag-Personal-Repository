CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    owner_id VARCHAR(100),
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    default_rag_strategy VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    mime_type VARCHAR(100),
    source_type VARCHAR(50) NOT NULL DEFAULT 'LOCAL_UPLOAD',
    source_path TEXT,
    parser_name VARCHAR(100),
    parser_version VARCHAR(50),
    status VARCHAR(32) NOT NULL DEFAULT 'UPLOADED',
    summary TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    parent_chunk_id UUID REFERENCES document_chunks(id) ON DELETE SET NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_strategy VARCHAR(100),
    page_number INTEGER,
    sheet_name VARCHAR(100),
    row_range VARCHAR(100),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_document_chunk_index UNIQUE (document_id, chunk_index)
);

CREATE TABLE chunk_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
    embedding_model VARCHAR(100) NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    session_status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB NOT NULL DEFAULT '[]'::jsonb,
    trace_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rag_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id VARCHAR(100) NOT NULL,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL,
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    rewritten_query TEXT,
    strategy_name VARCHAR(100),
    retriever_type VARCHAR(100),
    final_context TEXT,
    answer TEXT,
    model_name VARCHAR(100),
    prompt_name VARCHAR(100),
    prompt_version VARCHAR(50),
    latency_ms BIGINT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rag_retrieval_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES rag_runs(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE SET NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    rank INTEGER NOT NULL,
    score DOUBLE PRECISION,
    rerank_score DOUBLE PRECISION,
    retriever_type VARCHAR(100),
    source TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    selected_for_context BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rag_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES rag_runs(id) ON DELETE SET NULL,
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL,
    rating SMALLINT NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rag_feedback_rating CHECK (rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_documents_knowledge_base_id ON documents (knowledge_base_id);
CREATE INDEX idx_documents_status ON documents (status);
CREATE INDEX idx_documents_metadata_gin ON documents USING gin (metadata);
CREATE INDEX idx_document_chunks_document_id ON document_chunks (document_id);
CREATE INDEX idx_document_chunks_knowledge_base_id ON document_chunks (knowledge_base_id);
CREATE INDEX idx_document_chunks_metadata_gin ON document_chunks USING gin (metadata);
CREATE INDEX idx_chunk_embeddings_chunk_id ON chunk_embeddings (chunk_id);
CREATE INDEX idx_chunk_embeddings_embedding_hnsw
    ON chunk_embeddings
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunk_embeddings_metadata_gin ON chunk_embeddings USING gin (metadata);
CREATE INDEX idx_chat_messages_session_id_created_at ON chat_messages (session_id, created_at);
CREATE INDEX idx_rag_runs_trace_id ON rag_runs (trace_id);
CREATE INDEX idx_rag_runs_session_id ON rag_runs (session_id);
CREATE INDEX idx_rag_retrieval_results_run_id_rank ON rag_retrieval_results (run_id, rank);
CREATE INDEX idx_rag_feedback_run_id ON rag_feedback (run_id);
