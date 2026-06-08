package com.example.agentknowledge.dto.rag;

import java.time.Instant;
import java.util.UUID;

public record RagRunSummaryResponse(
        UUID id,
        String traceId,
        UUID sessionId,
        UUID messageId,
        UUID knowledgeBaseId,
        String question,
        String strategyName,
        String retrieverType,
        String modelName,
        Long latencyMs,
        String status,
        Instant createdAt
) {
}
