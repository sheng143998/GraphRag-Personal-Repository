package com.example.agentknowledge.dto.rag;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record RagRunResponse(
        UUID id,
        String traceId,
        UUID sessionId,
        UUID messageId,
        UUID knowledgeBaseId,
        String question,
        String rewrittenQuery,
        String strategyName,
        String retrieverType,
        String finalContext,
        String answer,
        String modelName,
        String promptName,
        String promptVersion,
        Long latencyMs,
        String status,
        String errorMessage,
        Instant createdAt,
        List<RetrievalResultResponse> retrievalResults
) {
    public record RetrievalResultResponse(
            UUID id,
            UUID chunkId,
            UUID documentId,
            Integer rank,
            Double score,
            Double rerankScore,
            String retrieverType,
            String source,
            Map<String, Object> metadata,
            Boolean selectedForContext
    ) {
    }
}
