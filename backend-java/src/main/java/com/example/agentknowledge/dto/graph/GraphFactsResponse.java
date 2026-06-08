package com.example.agentknowledge.dto.graph;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public record GraphFactsResponse(
        UUID knowledgeBaseId,
        String entity,
        int entityCount,
        int relationshipCount,
        List<EntityFact> entities,
        List<RelationshipFact> relationships
) {

    public record EntityFact(
            UUID id,
            UUID documentId,
            UUID chunkId,
            String name,
            String normalizedName,
            String entityType,
            String aliases,
            Map<String, Object> metadata,
            Instant createdAt,
            Instant updatedAt
    ) {
    }

    public record RelationshipFact(
            UUID id,
            UUID documentId,
            UUID chunkId,
            UUID sourceEntityId,
            UUID targetEntityId,
            String sourceName,
            String targetName,
            String relationType,
            Double confidence,
            Map<String, Object> metadata,
            Instant createdAt
    ) {
    }
}
