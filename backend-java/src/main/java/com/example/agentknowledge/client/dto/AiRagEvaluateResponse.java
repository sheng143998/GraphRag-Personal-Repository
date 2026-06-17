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
            @JsonProperty("recall_at_k") Double recallAtK,
            @JsonProperty("precision_at_k") Double precisionAtK,
            @JsonProperty("chunk_recall_at_k") Double chunkRecallAtK,
            @JsonProperty("document_recall_at_k") Double documentRecallAtK,
            @JsonProperty("evidence_recall_at_k") Double evidenceRecallAtK,
            Double mrr,
            @JsonProperty("citation_hit") Double citationHit,
            @JsonProperty("graph_entity_coverage") Double graphEntityCoverage,
            @JsonProperty("graph_relationship_hit") Double graphRelationshipHit,
            @JsonProperty("graph_expansion_term_hit") Double graphExpansionTermHit,
            List<String> notes
    ) {
    }
}
