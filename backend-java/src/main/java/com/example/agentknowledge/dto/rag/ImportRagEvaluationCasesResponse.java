package com.example.agentknowledge.dto.rag;

import java.util.List;
import java.util.UUID;

public record ImportRagEvaluationCasesResponse(
        UUID experimentId,
        int createdCount,
        int updatedCount,
        int failedCount,
        List<Item> items
) {
    public record Item(
            String caseId,
            String status,
            String errorMessage
    ) {
    }
}
