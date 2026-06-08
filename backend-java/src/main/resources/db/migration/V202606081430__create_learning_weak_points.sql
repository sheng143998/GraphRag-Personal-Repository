CREATE TABLE learning_weak_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL,
    evidence_message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL,
    topic VARCHAR(500) NOT NULL,
    expected_answer TEXT,
    source_hint TEXT,
    difficulty VARCHAR(32) NOT NULL DEFAULT 'medium',
    review_count INTEGER NOT NULL DEFAULT 1,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX uk_learning_weak_points_session_topic
    ON learning_weak_points (session_id, lower(topic));

CREATE INDEX idx_learning_weak_points_session_last_seen
    ON learning_weak_points (session_id, last_seen_at DESC);

CREATE INDEX idx_learning_weak_points_knowledge_base
    ON learning_weak_points (knowledge_base_id);
