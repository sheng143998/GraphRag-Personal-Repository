package com.example.agentknowledge.dto.rag;

import java.util.UUID;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RagQueryRequest(
        UUID knowledgeBaseId,
        UUID sessionId,
        UUID messageId,
        @NotBlank String question,
        @Size(max = 100) String strategyName,
        @Size(max = 100) String retrieverType,
        Integer topK
) {
}
