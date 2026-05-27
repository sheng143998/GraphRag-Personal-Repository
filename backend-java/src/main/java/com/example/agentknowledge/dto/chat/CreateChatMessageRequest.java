package com.example.agentknowledge.dto.chat;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateChatMessageRequest(
        @NotBlank @Size(max = 32) String role,
        @NotBlank String content,
        String citations
) {
}
