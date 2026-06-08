ALTER TABLE learning_weak_points
    ADD COLUMN mastery_status VARCHAR(32) NOT NULL DEFAULT 'NEEDS_REVIEW',
    ADD COLUMN last_assessed_at TIMESTAMPTZ;

CREATE INDEX idx_learning_weak_points_session_mastery
    ON learning_weak_points (session_id, mastery_status, last_seen_at DESC);
