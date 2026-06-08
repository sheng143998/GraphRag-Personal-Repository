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
@Table(name = "graph_relationships")
public class GraphRelationship {

    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @ManyToOne(optional = false)
    @JoinColumn(name = "knowledge_base_id", nullable = false)
    private KnowledgeBase knowledgeBase;

    @ManyToOne
    @JoinColumn(name = "document_id")
    private KnowledgeDocument document;

    @ManyToOne
    @JoinColumn(name = "chunk_id")
    private DocumentChunk chunk;

    @ManyToOne
    @JoinColumn(name = "source_entity_id")
    private GraphEntity sourceEntity;

    @ManyToOne
    @JoinColumn(name = "target_entity_id")
    private GraphEntity targetEntity;

    @Column(name = "source_name", nullable = false, length = 255)
    private String sourceName;

    @Column(name = "target_name", nullable = false, length = 255)
    private String targetName;

    @Column(name = "relation_type", nullable = false, length = 100)
    private String relationType = "co_occurs_with";

    @Column(nullable = false)
    private Double confidence = 0.5;

    @Column(nullable = false, columnDefinition = "jsonb")
    @JdbcTypeCode(SqlTypes.JSON)
    private Map<String, Object> metadata = new HashMap<>();

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
}
