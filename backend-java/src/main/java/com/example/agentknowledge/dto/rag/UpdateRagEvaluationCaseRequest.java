package com.example.agentknowledge.dto.rag;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.UUID;

public record UpdateRagEvaluationCaseRequest(
        UUID experimentId,
        @Size(max = 120) String caseId,
        String question,
        String expectedAnswer,
        List<UUID> relevantChunkIds,
        List<UUID> relevantDocumentIds,
        List<UUID> expectedCitationChunkIds,
        @Min(1) Integer evaluationTopK,
        String notes,
        String status
) {
}
