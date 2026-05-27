package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;
import java.util.UUID;

public record AiRagQueryRequest(
        String question,
        @JsonProperty("top_k") Integer topK,
        @JsonProperty("strategy_name") String strategyName,
        Context context
) {
    public record Context(
            @JsonProperty("knowledge_base_id") UUID knowledgeBaseId,
            @JsonProperty("session_id") UUID sessionId,
            @JsonProperty("message_id") UUID messageId,
            @JsonProperty("metadata_filters") Map<String, Object> metadataFilters
    ) {
    }
}
