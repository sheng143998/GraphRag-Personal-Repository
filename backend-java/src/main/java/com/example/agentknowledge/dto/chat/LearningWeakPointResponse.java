package com.example.agentknowledge.dto.chat;

import java.time.Instant;
import java.util.UUID;

public record LearningWeakPointResponse(
        UUID id,
        UUID sessionId,
        UUID knowledgeBaseId,
        UUID evidenceMessageId,
        String topic,
        String expectedAnswer,
        String sourceHint,
        String difficulty,
        String masteryStatus,
        Integer reviewCount,
        Instant lastSeenAt,
        Instant lastAssessedAt,
        Instant createdAt
) {
}
