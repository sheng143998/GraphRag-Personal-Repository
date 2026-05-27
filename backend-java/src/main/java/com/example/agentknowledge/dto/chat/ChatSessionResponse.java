package com.example.agentknowledge.dto.chat;

import java.time.Instant;
import java.util.UUID;

public record ChatSessionResponse(
        UUID id,
        UUID knowledgeBaseId,
        String title,
        String sessionStatus,
        Instant createdAt,
        Instant updatedAt
) {
}
