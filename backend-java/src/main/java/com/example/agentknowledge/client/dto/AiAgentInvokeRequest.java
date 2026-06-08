package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;
import java.util.UUID;

public record AiAgentInvokeRequest(
        @JsonProperty("agent_name") String agentName,
        @JsonProperty("user_input") String userInput,
        @JsonProperty("strategy_name") String strategyName,
        @JsonProperty("top_k") Integer topK,
        Context context,
        Map<String, Object> variables
) {
    public record Context(
            @JsonProperty("knowledge_base_id") UUID knowledgeBaseId,
            @JsonProperty("session_id") UUID sessionId,
            @JsonProperty("message_id") UUID messageId,
            @JsonProperty("metadata_filters") Map<String, Object> metadataFilters
    ) {
    }
}
