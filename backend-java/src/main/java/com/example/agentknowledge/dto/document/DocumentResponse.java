package com.example.agentknowledge.dto.document;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record DocumentResponse(
        UUID id,
        UUID knowledgeBaseId,
        String knowledgeBaseName,
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
        Integer chunkCount,
        List<DocumentChunkResponse> chunks,
        Instant createdAt,
        Instant updatedAt
) {
}
