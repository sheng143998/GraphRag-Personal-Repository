from __future__ import annotations

from app.agents.memory.models import MemoryEvaluationResult, MemoryRetrievalEvent


class MemoryEvaluator:
    """Scores whether retrieved memory was made available to the support run."""

    def evaluate(self, retrieval_event: MemoryRetrievalEvent | None) -> MemoryEvaluationResult:
        if retrieval_event is None:
            return MemoryEvaluationResult(notes=["No memory retrieval was attempted."])
        recalled = len(retrieval_event.matched_memories)
        used = len(retrieval_event.used_memory_ids)
        score = 0.0 if recalled == 0 else min(1.0, used / recalled)
        notes = []
        if recalled:
            notes.append("Retrieved memories were attached to support evidence and trace.")
        else:
            notes.append("No relevant memory matched the support context.")
        return MemoryEvaluationResult(
            recalled_count=recalled,
            used_count=used,
            memory_recall_score=score,
            notes=notes,
        )
