package com.example.agentknowledge.dto.chat;

import java.time.Instant;
import java.util.UUID;

public record ChatMessageResponse(
        UUID id,
        UUID sessionId,
        String role,
        String content,
        String citations,
        String traceId,
        Instant createdAt
) {
}
