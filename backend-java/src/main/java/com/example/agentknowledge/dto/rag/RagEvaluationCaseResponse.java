package com.example.agentknowledge.dto.rag;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record RagEvaluationCaseResponse(
        UUID id,
        UUID experimentId,
        String experimentName,
        String caseId,
        String question,
        String expectedAnswer,
        List<UUID> relevantChunkIds,
        List<UUID> relevantDocumentIds,
        List<UUID> expectedCitationChunkIds,
        Integer evaluationTopK,
        String notes,
        String status,
        Instant createdAt,
        Instant updatedAt
) {
}
