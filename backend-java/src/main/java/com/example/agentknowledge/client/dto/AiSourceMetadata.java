package com.example.agentknowledge.client.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;
import java.util.UUID;

public record AiSourceMetadata(
        @JsonProperty("document_id") UUID documentId,
        @JsonProperty("chunk_id") UUID chunkId,
        String title,
        @JsonProperty("source_path") String sourcePath,
        Double score,
        @JsonProperty("rerank_score") Double rerankScore,
        @JsonProperty("page_number") Integer pageNumber,
        @JsonProperty("sheet_name") String sheetName,
        Map<String, Object> metadata
) {
}
