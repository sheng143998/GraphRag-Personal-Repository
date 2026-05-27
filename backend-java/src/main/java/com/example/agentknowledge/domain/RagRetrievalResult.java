package com.example.agentknowledge.domain;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
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
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UuidGenerator;
import org.hibernate.type.SqlTypes;

@Getter
@Setter
@NoArgsConstructor
@Entity
@Table(name = "rag_retrieval_results")
public class RagRetrievalResult {

    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @ManyToOne(optional = false)
    @JoinColumn(name = "run_id", nullable = false)
    private RagRun run;

    @ManyToOne
    @JoinColumn(name = "chunk_id")
    private DocumentChunk chunk;

    @ManyToOne
    @JoinColumn(name = "document_id")
    private KnowledgeDocument document;

    @Column(nullable = false)
    private Integer rank;

    private Double score;

    @Column(name = "rerank_score")
    private Double rerankScore;

    @Column(name = "retriever_type", length = 100)
    private String retrieverType;

    @Column(columnDefinition = "TEXT")
    private String source;

    @Column(nullable = false, columnDefinition = "jsonb")
    @JdbcTypeCode(SqlTypes.JSON)
    private Map<String, Object> metadata = new HashMap<>();

    @Column(name = "selected_for_context", nullable = false)
    private Boolean selectedForContext = Boolean.FALSE;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
