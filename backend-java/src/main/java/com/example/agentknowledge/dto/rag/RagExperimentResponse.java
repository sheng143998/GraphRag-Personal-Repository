package com.example.agentknowledge.dto.rag;

import java.time.Instant;
import java.util.UUID;

public record RagExperimentResponse(
        UUID id,
        UUID knowledgeBaseId,
        String name,
        String description,
        String strategy,
        String datasetName,
        Integer sampleCount,
        Double precisionScore,
        Double recallScore,
        String precision,
        String recall,
        String status,
        String notes,
        Instant createdAt,
        Instant updatedAt
) {
}
