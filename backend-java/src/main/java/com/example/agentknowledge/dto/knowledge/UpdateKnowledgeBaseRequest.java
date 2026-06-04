package com.example.agentknowledge.dto.knowledge;

import jakarta.validation.constraints.Size;

public record UpdateKnowledgeBaseRequest(
        @Size(max = 200) String name,
        @Size(max = 5000) String description,
        @Size(max = 100) String ownerId,
        @Size(max = 32) String status,
        @Size(max = 100) String defaultRagStrategy
) {
}