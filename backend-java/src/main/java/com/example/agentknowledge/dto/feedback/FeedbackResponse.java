package com.example.agentknowledge.dto.feedback;

import java.time.Instant;
import java.util.UUID;

public record FeedbackResponse(
        UUID id,
        UUID runId,
        UUID sessionId,
        UUID messageId,
        Short rating,
        String feedbackType,
        String comment,
        Instant createdAt
) {
}
