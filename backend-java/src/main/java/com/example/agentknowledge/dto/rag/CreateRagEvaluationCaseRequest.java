package com.example.agentknowledge.dto.rag;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.UUID;

public record CreateRagEvaluationCaseRequest(
        @NotNull UUID experimentId,
        @NotBlank @Size(max = 120) String caseId,
        @NotBlank String question,
        String expectedAnswer,
        List<UUID> requiredChunkIds,
        List<UUID> supportingChunkIds,
        List<UUID> acceptableChunkIds,
        List<UUID> citationChunkIds,
        List<UUID> relevantChunkIds,
        List<UUID> relevantDocumentIds,
        List<UUID> expectedCitationChunkIds,
        @Min(1) Integer evaluationTopK,
        String notes,
        String status
) {
}
