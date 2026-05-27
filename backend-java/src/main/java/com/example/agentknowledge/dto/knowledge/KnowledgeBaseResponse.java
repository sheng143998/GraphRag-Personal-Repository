package com.example.agentknowledge.dto.knowledge;

import java.time.Instant;
import java.util.UUID;

public record KnowledgeBaseResponse(
        UUID id,
        String name,
        String description,
        String ownerId,
        String status,
        String defaultRagStrategy,
        Instant createdAt,
        Instant updatedAt
) {
}
