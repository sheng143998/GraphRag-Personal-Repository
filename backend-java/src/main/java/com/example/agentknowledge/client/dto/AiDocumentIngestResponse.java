package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.UUID;

public record AiDocumentIngestResponse(
        @JsonProperty("document_id") UUID documentId,
        @JsonProperty("chunk_count") Integer chunkCount,
        @JsonProperty("parser_name") String parserName,
        @JsonProperty("file_type") String fileType,
        AiTraceMetadata trace
) {
}
