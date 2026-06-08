ALTER TABLE learning_weak_points
    ADD COLUMN practice_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN last_practice_score DOUBLE PRECISION,
    ADD COLUMN next_review_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX idx_learning_weak_points_session_next_review
    ON learning_weak_points (session_id, next_review_at);
