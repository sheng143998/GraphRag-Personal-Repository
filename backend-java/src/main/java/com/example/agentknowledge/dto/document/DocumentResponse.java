package com.example.agentknowledge.dto.document;

import java.time.Instant;
import java.util.UUID;

public record DocumentResponse(
        UUID id,
        UUID knowledgeBaseId,
        String title,
        String documentType,
        String fileName,
        String fileType,
        String mimeType,
        String sourceType,
        String sourcePath,
        String parserName,
        String parserVersion,
        String status,
        String summary,
        String metadata,
        Instant createdAt,
        Instant updatedAt
) {
}
