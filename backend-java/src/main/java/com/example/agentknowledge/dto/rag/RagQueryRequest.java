package com.example.agentknowledge.dto.rag;

import java.util.Map;
import java.util.UUID;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record RagQueryRequest(
        @NotNull UUID knowledgeBaseId,
        UUID sessionId,
        UUID messageId,
        @NotBlank String question,
        @Size(max = 100) String strategyName,
        @Size(max = 100) String retrieverType,
        Map<String, Object> metadataFilters,
        Integer topK
) {
}
