package com.example.agentknowledge.dto.document;

import java.util.List;
import java.util.UUID;

public record DocumentBatchUploadResponse(
        UUID batchId,
        Integer acceptedCount,
        List<DocumentResponse> documents
) {
}
