package com.example.agentknowledge.dto.feedback;

import java.util.UUID;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateFeedbackRequest(
        UUID runId,
        UUID sessionId,
        UUID messageId,
        @NotNull @Min(1) @Max(5) Short rating,
        @NotBlank @Size(max = 50) String feedbackType,
        @Size(max = 5000) String comment
) {
}
