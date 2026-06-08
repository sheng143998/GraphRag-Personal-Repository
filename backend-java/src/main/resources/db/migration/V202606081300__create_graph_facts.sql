CREATE TABLE graph_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL DEFAULT 'concept',
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_graph_entity_chunk_name UNIQUE (chunk_id, normalized_name)
);

CREATE TABLE graph_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES document_chunks(id) ON DELETE CASCADE,
    source_entity_id UUID REFERENCES graph_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES graph_entities(id) ON DELETE CASCADE,
    source_name VARCHAR(255) NOT NULL,
    target_name VARCHAR(255) NOT NULL,
    relation_type VARCHAR(100) NOT NULL DEFAULT 'co_occurs_with',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_graph_relationship_chunk_pair UNIQUE (chunk_id, source_name, target_name, relation_type)
);

CREATE INDEX idx_graph_entities_kb_name ON graph_entities (knowledge_base_id, normalized_name);
CREATE INDEX idx_graph_entities_chunk_id ON graph_entities (chunk_id);
CREATE INDEX idx_graph_entities_metadata_gin ON graph_entities USING gin (metadata);
CREATE INDEX idx_graph_relationships_kb_source ON graph_relationships (knowledge_base_id, source_name);
CREATE INDEX idx_graph_relationships_kb_target ON graph_relationships (knowledge_base_id, target_name);
CREATE INDEX idx_graph_relationships_chunk_id ON graph_relationships (chunk_id);
CREATE INDEX idx_graph_relationships_metadata_gin ON graph_relationships USING gin (metadata);
