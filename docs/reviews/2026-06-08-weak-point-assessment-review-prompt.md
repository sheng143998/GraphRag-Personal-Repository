# Weak Point Assessment Review Prompt

Please review the weak point assessment change with focus on:

- `PATCH /api/chat/{sessionId}/weak-points/{weakPointId}` updates only the requested session-owned weak point.
- Only supported `masteryStatus` values are accepted: `MASTERED` and `NEEDS_REVIEW`.
- Frontend chat updates weak point state through Spring API only.
- The schema migration is additive and safe for existing weak point rows.
- Tests and smoke checks verify persisted update behavior.
