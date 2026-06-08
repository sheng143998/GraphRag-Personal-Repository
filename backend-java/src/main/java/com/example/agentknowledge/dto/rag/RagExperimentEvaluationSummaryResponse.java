package com.example.agentknowledge.dto.rag;

import java.util.List;
import java.util.UUID;

public record RagExperimentEvaluationSummaryResponse(
        int evaluationCount,
        Double averageGrounded,
        Double averageRetrieval,
        UUID bestExperimentId,
        String bestExperimentName,
        List<RagExperimentEvaluationHistoryResponse> recentEvaluations
) {
}
