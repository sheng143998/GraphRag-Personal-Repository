package com.example.agentknowledge.dto.document;

import java.util.UUID;

public record DocumentChunkResponse(
        UUID id,
        Integer chunkIndex,
        String title,
        String contentPreview,
        String chunkStrategy,
        Integer pageNumber,
        String sheetName,
        String rowRange,
        String metadata
) {
}
