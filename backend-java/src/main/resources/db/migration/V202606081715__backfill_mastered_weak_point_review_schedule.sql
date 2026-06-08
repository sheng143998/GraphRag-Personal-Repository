UPDATE learning_weak_points
SET next_review_at = COALESCE(last_assessed_at, last_seen_at, created_at, CURRENT_TIMESTAMP) + INTERVAL '7 days'
WHERE mastery_status = 'MASTERED'
  AND next_review_at <= CURRENT_TIMESTAMP;
