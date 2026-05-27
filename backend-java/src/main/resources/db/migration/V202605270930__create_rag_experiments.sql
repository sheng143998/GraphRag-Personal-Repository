CREATE TABLE rag_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    strategy_name VARCHAR(100) NOT NULL,
    dataset_name VARCHAR(200),
    sample_count INTEGER,
    precision_score DOUBLE PRECISION,
    recall_score DOUBLE PRECISION,
    status VARCHAR(32) NOT NULL DEFAULT 'PLANNED',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rag_experiments_updated_at ON rag_experiments (updated_at DESC);
CREATE INDEX idx_rag_experiments_strategy_name ON rag_experiments (strategy_name);
CREATE INDEX idx_rag_experiments_knowledge_base_id ON rag_experiments (knowledge_base_id);

INSERT INTO rag_experiments (
    name,
    description,
    strategy_name,
    dataset_name,
    sample_count,
    status,
    notes
) VALUES (
    '基础 RAG 基线',
    '用于记录 Basic RAG 第一版检索与回答质量的基线实验。',
    'basic-rag',
    '待配置评估集',
    0,
    'PLANNED',
    'precision 与 recall 暂未评估，后续接入评估集后回填。'
);
