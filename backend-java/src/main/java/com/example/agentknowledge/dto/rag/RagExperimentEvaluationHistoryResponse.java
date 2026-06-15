package com.example.agentknowledge.dto.rag;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record RagExperimentEvaluationHistoryResponse(
        UUID id,
        UUID experimentId,
        String experimentName,
        UUID runId,
        String runQuestion,
        String runStrategyName,
        String runRetrieverType,
        String runModelName,
        Long runLatencyMs,
        Instant runCreatedAt,
        Double groundedScore,
        Double retrievalScore,
        Double recallAtK,
        Double precisionAtK,
        Double mrr,
        Double citationHit,
        Double graphEntityCoverage,
        Double graphRelationshipHit,
        Double graphExpansionTermHit,
        Long latencyMs,
        Integer promptTokens,
        Integer completionTokens,
        Integer totalTokens,
        Integer embeddingTokens,
        Integer rerankTokens,
        Double estimatedCost,
        Long embeddingLatencyMs,
        Long retrievalLatencyMs,
        Long rerankLatencyMs,
        Long llmLatencyMs,
        Map<String, Object> tokenUsage,
        Map<String, Object> latencyBreakdown,
        Map<String, Object> strategyConfig,
        String expectedAnswer,
        String generatedAnswer,
        String notes,
        Instant createdAt
) {
}
