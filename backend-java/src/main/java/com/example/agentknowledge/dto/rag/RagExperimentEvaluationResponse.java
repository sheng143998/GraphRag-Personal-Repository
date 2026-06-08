package com.example.agentknowledge.dto.rag;

import java.util.List;

public record RagExperimentEvaluationResponse(
        RagExperimentResponse experiment,
        RagExperimentEvaluationHistoryResponse evaluation,
        Double groundedScore,
        Double retrievalScore,
        List<String> notes,
        List<RagExperimentEvaluationHistoryResponse> history
) {
}
