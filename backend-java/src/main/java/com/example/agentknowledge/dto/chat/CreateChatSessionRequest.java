package com.example.agentknowledge.dto.chat;

import java.util.UUID;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateChatSessionRequest(
        UUID knowledgeBaseId,
        @NotBlank @Size(max = 255) String title
) {
}
