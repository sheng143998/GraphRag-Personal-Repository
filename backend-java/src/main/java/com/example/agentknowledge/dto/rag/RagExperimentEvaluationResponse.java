package com.example.agentknowledge.dto.rag;

import java.util.List;

public record RagExperimentEvaluationResponse(
        RagExperimentResponse experiment,
        RagExperimentEvaluationHistoryResponse evaluation,
        Double groundedScore,
        Double retrievalScore,
        Double recallAtK,
        Double precisionAtK,
        Double chunkRecallAtK,
        Double documentRecallAtK,
        Double evidenceRecallAtK,
        Double mrr,
        Double citationHit,
        List<String> notes,
        List<RagExperimentEvaluationHistoryResponse> history
) {
}
