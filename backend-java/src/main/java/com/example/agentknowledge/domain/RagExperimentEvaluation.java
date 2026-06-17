package com.example.agentknowledge.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UuidGenerator;
import org.hibernate.type.SqlTypes;

@Getter
@Setter
@NoArgsConstructor
@Entity
@Table(name = "rag_experiment_evaluations")
public class RagExperimentEvaluation {

    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @ManyToOne
    @JoinColumn(name = "experiment_id", nullable = false)
    private RagExperiment experiment;

    @ManyToOne
    @JoinColumn(name = "run_id", nullable = false)
    private RagRun run;

    @Column(name = "grounded_score")
    private Double groundedScore;

    @Column(name = "retrieval_score")
    private Double retrievalScore;

    @Column(name = "recall_at_k")
    private Double recallAtK;

    @Column(name = "precision_at_k")
    private Double precisionAtK;

    @Column(name = "chunk_recall_at_k")
    private Double chunkRecallAtK;

    @Column(name = "document_recall_at_k")
    private Double documentRecallAtK;

    @Column(name = "evidence_recall_at_k")
    private Double evidenceRecallAtK;

    @Column(name = "mrr")
    private Double mrr;

    @Column(name = "citation_hit")
    private Double citationHit;

    @Column(name = "graph_entity_coverage")
    private Double graphEntityCoverage;

    @Column(name = "graph_relationship_hit")
    private Double graphRelationshipHit;

    @Column(name = "graph_expansion_term_hit")
    private Double graphExpansionTermHit;

    @Column(name = "latency_ms")
    private Long latencyMs;

    @Column(name = "prompt_tokens")
    private Integer promptTokens;

    @Column(name = "completion_tokens")
    private Integer completionTokens;

    @Column(name = "total_tokens")
    private Integer totalTokens;

    @Column(name = "embedding_tokens")
    private Integer embeddingTokens;

    @Column(name = "rerank_tokens")
    private Integer rerankTokens;

    @Column(name = "estimated_cost")
    private Double estimatedCost;

    @Column(name = "embedding_latency_ms")
    private Long embeddingLatencyMs;

    @Column(name = "retrieval_latency_ms")
    private Long retrievalLatencyMs;

    @Column(name = "rerank_latency_ms")
    private Long rerankLatencyMs;

    @Column(name = "llm_latency_ms")
    private Long llmLatencyMs;

    @Column(name = "token_usage", nullable = false, columnDefinition = "jsonb")
    @JdbcTypeCode(SqlTypes.JSON)
    private Map<String, Object> tokenUsage = new HashMap<>();

    @Column(name = "latency_breakdown", nullable = false, columnDefinition = "jsonb")
    @JdbcTypeCode(SqlTypes.JSON)
    private Map<String, Object> latencyBreakdown = new HashMap<>();

    @Column(name = "strategy_config", nullable = false, columnDefinition = "jsonb")
    @JdbcTypeCode(SqlTypes.JSON)
    private Map<String, Object> strategyConfig = new HashMap<>();

    @Column(name = "expected_answer", columnDefinition = "TEXT")
    private String expectedAnswer;

    @Column(name = "generated_answer", columnDefinition = "TEXT")
    private String generatedAnswer;

    @Column(columnDefinition = "TEXT")
    private String notes;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
