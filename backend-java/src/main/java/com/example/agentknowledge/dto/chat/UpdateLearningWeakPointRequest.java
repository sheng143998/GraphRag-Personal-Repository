package com.example.agentknowledge.dto.chat;

import jakarta.validation.constraints.NotBlank;

public record UpdateLearningWeakPointRequest(
        @NotBlank String masteryStatus
) {
}
