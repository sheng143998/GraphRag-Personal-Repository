package com.example.agentknowledge.dto.rag;

import java.util.List;
import java.util.UUID;

public record RagQueryResponse(
        UUID runId,
        String traceId,
        String status,
        String answer,
        List<String> citations,
        String strategyName,
        String retrieverType
) {
}
