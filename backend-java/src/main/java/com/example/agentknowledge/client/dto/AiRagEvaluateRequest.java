package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record AiRagEvaluateRequest(
        String question,
        @JsonProperty("expected_answer") String expectedAnswer,
        @JsonProperty("generated_answer") String generatedAnswer,
        List<AiSourceMetadata> citations,
        @JsonProperty("strategy_name") String strategyName,
        Context context,
        @JsonProperty("evaluation_case") EvaluationCase evaluationCase
) {
    public record Context(
            @JsonProperty("knowledge_base_id") UUID knowledgeBaseId,
            @JsonProperty("session_id") UUID sessionId,
            @JsonProperty("message_id") UUID messageId,
            @JsonProperty("metadata_filters") Map<String, Object> metadataFilters
    ) {
    }

    public record EvaluationCase(
            @JsonProperty("case_id") String caseId,
            @JsonProperty("relevant_chunk_ids") List<UUID> relevantChunkIds,
            @JsonProperty("relevant_document_ids") List<UUID> relevantDocumentIds,
            @JsonProperty("expected_citation_chunk_ids") List<UUID> expectedCitationChunkIds,
            @JsonProperty("top_k") Integer topK
    ) {
    }
}
