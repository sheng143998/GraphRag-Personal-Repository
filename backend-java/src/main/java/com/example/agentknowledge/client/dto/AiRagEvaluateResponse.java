package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record AiRagEvaluateResponse(
        Result result,
        AiTraceMetadata trace
) {
    public record Result(
            @JsonProperty("grounded_score") Double groundedScore,
            @JsonProperty("retrieval_score") Double retrievalScore,
            List<String> notes
    ) {
    }
}
