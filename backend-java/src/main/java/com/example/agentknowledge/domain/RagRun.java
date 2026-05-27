package com.example.agentknowledge.domain;

import java.time.Instant;
import java.util.UUID;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UuidGenerator;

@Getter
@Setter
@NoArgsConstructor
@Entity
@Table(name = "rag_runs")
public class RagRun {

    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @Column(name = "trace_id", nullable = false, length = 100)
    private String traceId;

    @ManyToOne
    @JoinColumn(name = "session_id")
    private ChatSession session;

    @ManyToOne
    @JoinColumn(name = "message_id")
    private ChatMessage message;

    @ManyToOne
    @JoinColumn(name = "knowledge_base_id")
    private KnowledgeBase knowledgeBase;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String question;

    @Column(name = "rewritten_query", columnDefinition = "TEXT")
    private String rewrittenQuery;

    @Column(name = "strategy_name", length = 100)
    private String strategyName;

    @Column(name = "retriever_type", length = 100)
    private String retrieverType;

    @Column(name = "final_context", columnDefinition = "TEXT")
    private String finalContext;

    @Column(columnDefinition = "TEXT")
    private String answer;

    @Column(name = "model_name", length = 100)
    private String modelName;

    @Column(name = "prompt_name", length = 100)
    private String promptName;

    @Column(name = "prompt_version", length = 50)
    private String promptVersion;

    @Column(name = "latency_ms")
    private Long latencyMs;

    @Column(nullable = false, length = 32)
    private String status = "PENDING";

    @Column(name = "error_message", columnDefinition = "TEXT")
    private String errorMessage;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
